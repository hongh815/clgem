"""Pairwise parallel-safety checks for scoped Cogem tasks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .contracts import TaskRecord


@dataclass(frozen=True, slots=True)
class ParallelAssessment:
    task_a: str
    task_b: str
    parallel_safe: bool
    reason_codes: tuple[str, ...]
    details: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "task_a": self.task_a,
            "task_b": self.task_b,
            "parallel_safe": self.parallel_safe,
            "reason_codes": list(self.reason_codes),
            "details": list(self.details),
        }


def _transitive_dependencies(task_id: str, tasks: Mapping[str, TaskRecord]) -> set[str]:
    seen: set[str] = set()
    stack = list(tasks.get(task_id).depends_on if task_id in tasks else ())
    while stack:
        dependency = stack.pop()
        if dependency in seen:
            continue
        seen.add(dependency)
        referenced = tasks.get(dependency)
        if referenced is not None:
            stack.extend(referenced.depends_on)
    return seen


def assess_parallel_safety(
    task_a: TaskRecord,
    task_b: TaskRecord,
    tasks: Mapping[str, TaskRecord],
) -> ParallelAssessment:
    reasons: list[str] = []
    details: list[str] = []

    if task_a.task_id == task_b.task_id:
        reasons.append("SAME_TASK")
        details.append("A task cannot be scheduled in parallel with itself.")

    if task_a.source_write and not task_a.write_set or task_b.source_write and not task_b.write_set:
        reasons.append("MISSING_SCOPE")
        details.append("Each source-writing task must declare a non-empty write_set.")

    write_write = sorted(set(task_a.write_set) & set(task_b.write_set))
    if write_write:
        reasons.append("WRITE_WRITE_CONFLICT")
        details.append(f"Both tasks write: {', '.join(write_write)}")

    write_read = sorted((set(task_a.write_set) & set(task_b.read_set)) | (set(task_b.write_set) & set(task_a.read_set)))
    if write_read:
        reasons.append("WRITE_READ_CONFLICT")
        details.append(f"One task writes paths read by the other: {', '.join(write_read)}")

    deps_a = _transitive_dependencies(task_a.task_id, tasks)
    deps_b = _transitive_dependencies(task_b.task_id, tasks)
    if task_b.task_id in deps_a or task_a.task_id in deps_b:
        reasons.append("DEPENDENCY_CONFLICT")
        details.append("A direct or transitive dependency requires sequential execution.")

    core_overlap = sorted(set(task_a.core_impact_set) & set(task_b.core_impact_set))
    if core_overlap:
        reasons.append("CORE_IMPACT_CONFLICT")
        details.append(f"Both tasks impact core paths: {', '.join(core_overlap)}")

    if task_a.writing_lease == task_b.writing_lease:
        reasons.append("LEASE_CONFLICT")
        details.append(f"Both tasks use writing lease {task_a.writing_lease!r}.")

    ordered_codes = tuple(dict.fromkeys(reasons))
    return ParallelAssessment(
        task_a=task_a.task_id,
        task_b=task_b.task_id,
        parallel_safe=not ordered_codes,
        reason_codes=ordered_codes,
        details=tuple(details),
    )
