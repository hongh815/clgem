#!/usr/bin/env python3
"""Create a deterministic portable Cogem archive with manifest-enforced skills."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPT_DIR = Path(__file__).resolve().parent
filtered = []
for entry in sys.path:
    try:
        resolved = Path(entry or ".").resolve()
    except OSError:
        filtered.append(entry)
        continue
    if resolved in {SRC.resolve(), SCRIPT_DIR.resolve()}:
        continue
    filtered.append(entry)
sys.path[:] = [str(SRC), *filtered]

from cogem.skill_policy import validate_skills  # noqa: E402


_EXCLUDED_DIRS = {".git", ".graph", ".venv", "venv", "__pycache__", "build", "dist", ".pytest_cache"}
_EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}
_LIVE_STATE_DIRS = {"goals", "tasks", "messages", "decisions", "handoffs", "reports", "snapshots"}


class ManifestError(ValueError):
    """Raised when a skill distribution manifest is incomplete or unsafe."""


def _include(relative: Path) -> bool:
    if any(part in _EXCLUDED_DIRS for part in relative.parts):
        return False
    if relative.suffix in _EXCLUDED_SUFFIXES:
        return False
    if relative.name == ".env":
        return False
    return True


def _validate_skill_manifests(root: Path) -> None:
    issues = validate_skills(root)
    if not issues:
        return
    details = "; ".join(f"{issue.code} [{issue.path}]: {issue.message}" for issue in issues)
    raise ManifestError(details)


def _validate_release_state(root: Path) -> None:
    state_root = root / ".agents"
    live: list[str] = []
    for name in sorted(_LIVE_STATE_DIRS):
        directory = state_root / name
        if not directory.exists():
            continue
        live.extend(path.relative_to(root).as_posix() for path in sorted(directory.glob("*.json")))
    if live:
        raise ManifestError(
            "portable releases must not contain live coordination or scope records: " + ", ".join(live)
        )


def collect_distribution_files(root: Path) -> list[Path]:
    """Collect all distributable kit files after enforcing every skill manifest."""

    root = Path(root).resolve()
    _validate_skill_manifests(root)
    _validate_release_state(root)
    files = [path for path in root.rglob("*") if path.is_file() and _include(path.relative_to(root))]
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def create_archive(root: Path, destination: Path) -> Path:
    root = Path(root).resolve()
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    prefix = root.name
    files = collect_distribution_files(root)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(root)
            info = zipfile.ZipInfo(f"{prefix}/{relative.as_posix()}")
            info.date_time = (2026, 7, 16, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a portable Cogem ZIP archive.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="../multi-agent-graphify-kit-v5.0.0.zip")
    args = parser.parse_args()
    try:
        archive = create_archive(Path(args.root), Path(args.output))
    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
