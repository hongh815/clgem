"""Shared task path and risk classification rules."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Protocol


class _TaskLike(Protocol):
    task_id: str
    write_set: tuple[str, ...]
    review_level: str


def _normalize(value: str) -> PurePosixPath:
    text = str(value).strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return PurePosixPath(text)


def is_under(path: str, root: str) -> bool:
    """Return whether a project-relative path is the root or lies below it."""

    candidate = _normalize(path)
    parent = _normalize(root)
    if candidate.is_absolute() or parent.is_absolute():
        return False
    candidate_parts = candidate.parts
    parent_parts = parent.parts
    if any(part in {".", ".."} for part in (*candidate_parts, *parent_parts)):
        return False
    return bool(parent_parts) and candidate_parts[: len(parent_parts)] == parent_parts


def task_touches_skill(task: _TaskLike) -> bool:
    """Classify tasks that may write the Skill tree."""

    return any(is_under(path, "skills") for path in task.write_set)


def skill_review_level_message(task: _TaskLike) -> str:
    """Return the canonical error text for an under-classified Skill task."""

    return f"{task.task_id} writes under skills/ and must declare review_level 'high-risk'."
