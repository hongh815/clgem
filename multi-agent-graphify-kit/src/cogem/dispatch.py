"""Dispatch authorization checks for scoped worker tasks."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .config import load_config
from .contracts import ContractError
from .graph import build_project_graph
from .model_policy import load_model_policy
from .scope import ScopeError, record_dispatch_snapshot
from .state import load_state
from .task_policy import skill_review_level_message, task_touches_skill
from .validation import validate_project


_DISPATCH_STATUSES = {"assigned", "in_progress"}
_DEPENDENCY_COMPLETE = {"integrated", "closed"}
_ACTIVE_LEASE_STATUSES = {"assigned", "in_progress", "blocked", "review_ready", "review_failed"}


@dataclass(frozen=True, slots=True)
class DispatchResult:
    task_id: str
    allowed: bool
    reasons: tuple[str, ...]
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "allowed": self.allowed,
            "reason_codes": list(self.reason_codes),
            "reasons": list(self.reasons),
        }


def check_dispatch(root: Path, task_id: str, *, record_snapshot: bool = False) -> DispatchResult:
    root = Path(root).resolve()
    config = load_config(root)
    state = load_state(root, config["state_dir"])
    task = state.tasks.get(task_id)
    if task is None:
        raise ContractError(f"task not found: {task_id}")

    findings: list[tuple[str, str]] = []
    if task.status not in _DISPATCH_STATUSES:
        findings.append(("TASK_NOT_ASSIGNED", f"Task status must be assigned or in_progress; got {task.status}."))
    if task.source_write and not task.write_set:
        findings.append(("WRITE_SET_EMPTY", "A source-writing task must declare at least one write_set path."))
    if not task.writing_lease.strip():
        findings.append(("WRITING_LEASE_MISSING", "A dispatchable task requires a writing lease."))
    if task_touches_skill(task) and task.review_level != "high-risk":
        findings.append(("SKILL_REVIEW_LEVEL_REQUIRED", skill_review_level_message(task)))

    for dependency_id in task.depends_on:
        dependency = state.tasks.get(dependency_id)
        if dependency is None or dependency.status not in _DEPENDENCY_COMPLETE:
            status = dependency.status if dependency else "missing"
            findings.append(("DEPENDENCY_NOT_COMPLETE", f"Dependency {dependency_id} is {status}; expected integrated or closed."))

    for other in state.tasks.values():
        if other.task_id == task.task_id or other.status not in _ACTIVE_LEASE_STATUSES:
            continue
        if other.writing_lease == task.writing_lease:
            findings.append(("WRITING_LEASE_CONFLICT", f"Writing lease is also used by active task {other.task_id}."))

    policy_path = root / config["model_policy_file"]
    if policy_path.exists():
        policy = load_model_policy(policy_path)
        role = policy.roles.get(task.owner)
        if role is None:
            findings.append(("UNKNOWN_TASK_OWNER", f"Role {task.owner!r} is absent from the engine policy."))
        elif task.source_write and role.permissions != "scoped-write":
            findings.append(("ROLE_SOURCE_WRITE_NOT_ALLOWED", f"Role {task.owner!r} has permission class {role.permissions!r}."))

    graph_fingerprint: str | None = None
    graph_path = root / config["graph_dir"] / "project-graph.json"
    if not graph_path.is_file():
        findings.append(("GRAPH_NOT_GENERATED", f"Generate {graph_path.relative_to(root).as_posix()} before dispatch."))
    else:
        try:
            stored = json.loads(graph_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(("GRAPH_INVALID", f"Stored graph is unreadable: {exc}."))
        else:
            graph_fingerprint = stored.get("input_fingerprint") if isinstance(stored.get("input_fingerprint"), str) else None
            current = build_project_graph(root, state, config)
            if graph_fingerprint != current.get("input_fingerprint"):
                findings.append(("GRAPH_STALE", "Project inputs changed after graph generation; regenerate the graph."))

    for diagnostic in validate_project(root):
        if diagnostic.severity != "error":
            continue
        if diagnostic.code == "SKILL_REVIEW_LEVEL_REQUIRED":
            findings.append((diagnostic.code, diagnostic.message))
        else:
            findings.append((f"PROJECT_{diagnostic.code}", diagnostic.message))

    if not findings and record_snapshot:
        try:
            record_dispatch_snapshot(root, task, graph_fingerprint or "missing")
        except ScopeError as exc:
            findings.append(("SCOPE_SNAPSHOT_INVALID", str(exc)))

    unique: dict[tuple[str, str], None] = {}
    for item in findings:
        unique[item] = None
    ordered = tuple(unique)
    return DispatchResult(
        task_id=task_id,
        allowed=not ordered,
        reason_codes=tuple(code for code, _ in ordered),
        reasons=tuple(message for _, message in ordered),
    )
