"""Generic authoring and distribution policy for every skill under ``skills/``."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
from typing import Mapping


_SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ALLOWED_ROOT_ENTRIES = {
    "SKILL.md",
    "manifest.txt",
    "agents",
    "assets",
    "references",
    "scripts",
    "schemas",
    "tests",
}
_TRANSIENT_DIRS = {"__pycache__", ".pytest_cache"}
_TRANSIENT_SUFFIXES = {".pyc", ".pyo"}
_REQUIRED_MANIFEST_ENTRIES = {"SKILL.md", "manifest.txt"}
_DIRECTORY_ROOT_ENTRIES = _ALLOWED_ROOT_ENTRIES - _REQUIRED_MANIFEST_ENTRIES


class SkillPolicyError(ValueError):
    """Raised when a skill manifest cannot be interpreted safely."""


@dataclass(frozen=True, slots=True)
class SkillIssue:
    severity: str
    code: str
    message: str
    path: str


@dataclass(frozen=True, slots=True)
class SkillMetadata:
    name: str
    description: str


def validate_skill_name(name: str) -> str:
    """Validate and return a portable Skill directory/frontmatter name."""

    value = str(name).strip()
    if len(value) >= 64 or not _SKILL_NAME.fullmatch(value):
        raise SkillPolicyError(
            "Skill names must contain 1-63 lowercase letters, numbers, or hyphen-separated tokens"
        )
    return value


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_skill_frontmatter(path: Path) -> SkillMetadata:
    """Parse the required scalar fields without introducing a YAML dependency."""

    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SkillPolicyError("SKILL.md must start with a YAML frontmatter delimiter (---)")
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise SkillPolicyError("SKILL.md frontmatter is missing its closing delimiter (---)") from exc

    fields: dict[str, str] = {}
    for raw in lines[1:end]:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise SkillPolicyError(f"unsupported frontmatter line: {raw!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        scalar = value.strip()
        if not key or key in fields:
            raise SkillPolicyError(f"duplicate or empty frontmatter field: {key!r}")
        if scalar in {">", ">-", ">+", "|", "|-", "|+"}:
            raise SkillPolicyError("frontmatter fields must use single-line scalar values")
        fields[key] = _unquote(value)

    expected = {"name", "description"}
    unknown = sorted(set(fields) - expected)
    if unknown:
        raise SkillPolicyError(
            f"SKILL.md frontmatter contains unsupported field(s): {', '.join(unknown)}"
        )
    missing = [key for key in ("name", "description") if not fields.get(key, "").strip()]
    if missing:
        raise SkillPolicyError(f"SKILL.md frontmatter is missing required field(s): {', '.join(missing)}")
    return SkillMetadata(
        name=validate_skill_name(fields["name"]),
        description=fields["description"].strip(),
    )


def _normalize_manifest_entry(raw: str) -> str:
    value = raw.strip().replace("\\", "/")
    if not value:
        raise SkillPolicyError("manifest entries must not be empty")
    path = PurePosixPath(value)
    if path.is_absolute() or value.startswith("/") or ".." in path.parts:
        raise SkillPolicyError(f"manifest path must remain inside the skill directory: {raw!r}")
    normalized = path.as_posix()
    if normalized in {"", "."}:
        raise SkillPolicyError(f"invalid manifest path: {raw!r}")
    return normalized


def load_skill_manifest(skill_dir: Path) -> tuple[str, ...]:
    """Load a skill's authoritative distribution list."""

    skill_dir = Path(skill_dir)
    manifest = skill_dir / "manifest.txt"
    if not manifest.is_file():
        raise SkillPolicyError("manifest.txt is required")
    entries: list[str] = []
    for line_number, raw in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            entry = _normalize_manifest_entry(stripped)
        except SkillPolicyError as exc:
            raise SkillPolicyError(f"manifest.txt line {line_number}: {exc}") from exc
        if entry in entries:
            raise SkillPolicyError(f"manifest.txt contains duplicate entry: {entry}")
        entries.append(entry)
    if not entries:
        raise SkillPolicyError("manifest.txt must contain at least SKILL.md and manifest.txt")
    return tuple(entries)


def _actual_skill_files(skill_dir: Path) -> set[str]:
    files: set[str] = set()
    for path in sorted(skill_dir.rglob("*")):
        relative = path.relative_to(skill_dir)
        if any(part in _TRANSIENT_DIRS for part in relative.parts):
            continue
        if path.is_file() and path.suffix not in _TRANSIENT_SUFFIXES:
            files.add(relative.as_posix())
    return files


def _issue(code: str, message: str, path: Path, root: Path) -> SkillIssue:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        relative = path.as_posix()
    return SkillIssue("error", code, message, relative)


def validate_skills(root: Path) -> list[SkillIssue]:
    """Validate every immediate skill directory under ``skills/``."""

    root = Path(root).resolve()
    skills_root = root / "skills"
    if not skills_root.exists():
        return []

    issues: list[SkillIssue] = []
    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir() and not path.name.startswith(".")):
        name = skill_dir.name
        try:
            validate_skill_name(name)
        except SkillPolicyError as exc:
            issues.append(_issue("SKILL_DIRECTORY_NAME", str(exc), skill_dir, root))

        unexpected = sorted(child.name for child in skill_dir.iterdir() if child.name not in _ALLOWED_ROOT_ENTRIES and child.name not in _TRANSIENT_DIRS)
        if unexpected:
            issues.append(_issue("SKILL_ROOT_LAYOUT", f"Unexpected skill-root entries: {', '.join(unexpected)}.", skill_dir, root))
        wrong_types = sorted(
            child.name
            for child in skill_dir.iterdir()
            if child.name in _DIRECTORY_ROOT_ENTRIES and not child.is_dir()
        )
        if wrong_types:
            issues.append(
                _issue(
                    "SKILL_ROOT_ENTRY_TYPE",
                    f"Optional Skill root entries must be directories: {', '.join(wrong_types)}.",
                    skill_dir,
                    root,
                )
            )

        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            issues.append(_issue("SKILL_FILE_MISSING", "SKILL.md is required.", skill_file, root))
        else:
            try:
                metadata = parse_skill_frontmatter(skill_file)
            except (OSError, UnicodeError, SkillPolicyError) as exc:
                issues.append(_issue("SKILL_FRONTMATTER_INVALID", str(exc), skill_file, root))
            else:
                if metadata.name != name:
                    issues.append(_issue("SKILL_NAME_MISMATCH", f"Frontmatter name {metadata.name!r} must match directory {name!r}.", skill_file, root))
                if not metadata.description.startswith("Use when"):
                    issues.append(_issue("SKILL_DESCRIPTION_TRIGGER", "Frontmatter description must start with 'Use when'.", skill_file, root))

        try:
            manifest_entries = set(load_skill_manifest(skill_dir))
        except (OSError, UnicodeError, SkillPolicyError) as exc:
            issues.append(_issue("SKILL_MANIFEST_INVALID", str(exc), skill_dir / "manifest.txt", root))
            manifest_entries = set()

        if manifest_entries:
            missing_required = sorted(_REQUIRED_MANIFEST_ENTRIES - manifest_entries)
            if missing_required:
                issues.append(_issue("SKILL_MANIFEST_REQUIRED_ENTRY", f"manifest.txt must include: {', '.join(missing_required)}.", skill_dir / "manifest.txt", root))
            actual_files = _actual_skill_files(skill_dir)
            for entry in sorted(manifest_entries - actual_files):
                issues.append(_issue("SKILL_MANIFEST_MISSING_FILE", f"Manifest entry does not exist: {entry}.", skill_dir / entry, root))
            for entry in sorted(actual_files - manifest_entries):
                issues.append(_issue("SKILL_UNLISTED_FILE", f"Skill file is absent from manifest.txt: {entry}.", skill_dir / entry, root))

        schema_dir = skill_dir / "schemas"
        if schema_dir.exists():
            for schema in sorted(schema_dir.rglob("*.json")):
                try:
                    raw = json.loads(schema.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                    issues.append(_issue("SKILL_SCHEMA_INVALID_JSON", f"Schema is not valid JSON: {exc}.", schema, root))
                    continue
                if not isinstance(raw, Mapping) or raw.get("$schema") is None or raw.get("type") != "object":
                    issues.append(_issue("SKILL_SCHEMA_INVALID_SHAPE", "Schema must declare $schema and have object as its root type.", schema, root))

    return sorted(issues, key=lambda item: (item.code, item.path, item.message))
