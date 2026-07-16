"""Deterministic hashes used for graph freshness and independent-review evidence."""

from __future__ import annotations

import fnmatch
import hashlib
from pathlib import Path
from typing import Iterable


_BASE_IGNORES = (
    ".git/**",
    ".graph/**",
    ".venv/**",
    "venv/**",
    "build/**",
    "dist/**",
    "__pycache__/**",
    "**/__pycache__/**",
    "*.pyc",
    "**/*.pyc",
    "*.pyo",
    "**/*.pyo",
    "*.zip",
    ".env",
)
_GRAPH_VOLATILE = (
    "Comm.md",
    ".agents/messages/**",
    ".agents/reports/**",
    ".agents/snapshots/**",
)
_REVIEW_VOLATILE = (
    "Comm.md",
    ".agents/**",
)


def _matches(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(f"{path}/", pattern) for pattern in patterns)


def _hash_paths(root: Path, relative_paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(set(relative_paths)):
        path = root / relative
        if not path.is_file() or path.is_symlink():
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def graph_input_fingerprint(root: Path, relative_files: Iterable[str]) -> str:
    """Hash inputs that must remain stable between graph generation and dispatch."""

    root = Path(root).resolve()
    included = [
        path for path in relative_files
        if not _matches(path, (*_BASE_IGNORES, *_GRAPH_VOLATILE))
    ]
    return _hash_paths(root, included)


def review_tree_hash(root: Path) -> str:
    """Hash reviewable project artifacts while excluding coordination and generated state."""

    root = Path(root).resolve()
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        if _matches(relative, (*_BASE_IGNORES, *_REVIEW_VOLATILE)):
            continue
        files.append(relative)
    return _hash_paths(root, files)
