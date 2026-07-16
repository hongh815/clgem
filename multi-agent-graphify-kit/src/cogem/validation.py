"""Integrated validation for Cogem state, references, scopes, and engine policy."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from .config import ConfigError, load_config
from .contracts import ContractError
from .graph import build_project_graph
from .goal import assess_goal
from .evidence import review_tree_hash
from .model_policy import ModelPolicyError, load_model_policy, resolve_role_engines
from .parallel import assess_parallel_safety
from .state import CogemState, load_state
from .scope import ScopeError, load_scope_snapshot
from .skill_policy import validate_skills
from .task_policy import skill_review_level_message, task_touches_skill


@dataclass(frozen=True, slots=True)
class Diagnostic:
    severity: str
    code: str
    message: str
    path: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {"severity": self.severity, "code": self.code, "message": self.message, "path": self.path}


_ACTIVE_EXECUTION_STATUSES = {"assigned", "in_progress", "blocked", "review_ready", "review_failed"}


def _dependency_cycles(state: CogemState) -> list[list[str]]:
    cycles: list[list[str]] = []
    visited: set[str] = set()
    active: set[str] = set()
    stack: list[str] = []

    def visit(task_id: str) -> None:
        if task_id in active:
            start = stack.index(task_id)
            cycle = stack[start:] + [task_id]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if task_id in visited:
            return
        visited.add(task_id)
        active.add(task_id)
        stack.append(task_id)
        task = state.tasks.get(task_id)
        if task:
            for dependency in task.depends_on:
                if dependency in state.tasks:
                    visit(dependency)
        stack.pop()
        active.remove(task_id)

    for task_id in state.tasks:
        visit(task_id)
    return cycles


def _validate_schema_files(root: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    schema_dir = root / "skills" / "cogem" / "schemas"
    if not schema_dir.exists():
        return diagnostics
    for path in sorted(schema_dir.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            diagnostics.append(Diagnostic("error", "INVALID_SCHEMA_JSON", f"{exc.msg} at line {exc.lineno}, column {exc.colno}", path.relative_to(root).as_posix()))
            continue
        if not isinstance(raw, Mapping) or raw.get("$schema") is None or raw.get("type") != "object":
            diagnostics.append(Diagnostic("error", "INVALID_SCHEMA_SHAPE", "Schema must declare $schema and use object as its root type.", path.relative_to(root).as_posix()))
    return diagnostics


def validate_project(
    root: Path,
    *,
    model_policy_required: bool = True,
    require_engines: bool = False,
    require_models: bool | None = None,
) -> list[Diagnostic]:
    root = Path(root).resolve()
    if require_models is not None:
        require_engines = require_models
    diagnostics: list[Diagnostic] = []
    try:
        config = load_config(root)
    except ConfigError as exc:
        return [Diagnostic("error", "CONFIG_ERROR", str(exc), "cogem.config.json")]

    try:
        state = load_state(root, config["state_dir"])
    except ContractError as exc:
        return [Diagnostic("error", "CONTRACT_ERROR", str(exc), config["state_dir"])]

    for goal in state.goals.values():
        for task_id in goal.task_ids:
            if task_id not in state.tasks:
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "MISSING_GOAL_TASK",
                        f"{goal.goal_id} references missing task {task_id}.",
                        f"{config['state_dir']}/goals",
                    )
                )
        if goal.status == "blocked" and not goal.blocker:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "GOAL_BLOCKER_REQUIRED",
                    f"{goal.goal_id} is blocked but has no blocker description.",
                    f"{config['state_dir']}/goals",
                )
            )
        if goal.status != "blocked" and goal.blocker:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "GOAL_BLOCKER_STATE_MISMATCH",
                    f"{goal.goal_id} has a blocker description but status is {goal.status}.",
                    f"{config['state_dir']}/goals",
                )
            )
        if goal.status == "achieved":
            result = assess_goal(root, goal.goal_id)
            if result.next_action != "complete":
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "GOAL_NOT_COMPLETE",
                        f"{goal.goal_id} is marked achieved but goal-check requires {result.next_action}.",
                        f"{config['state_dir']}/goals",
                    )
                )

    for task in state.tasks.values():
        if task_touches_skill(task) and task.review_level != "high-risk":
            diagnostics.append(
                Diagnostic(
                    "error",
                    "SKILL_REVIEW_LEVEL_REQUIRED",
                    skill_review_level_message(task),
                    f"{config['state_dir']}/tasks",
                )
            )
        for dependency in task.depends_on:
            if dependency not in state.tasks:
                diagnostics.append(Diagnostic("error", "MISSING_TASK_DEPENDENCY", f"{task.task_id} depends on missing task {dependency}.", f"{config['state_dir']}/tasks"))
        if task.task_id in task.depends_on:
            diagnostics.append(Diagnostic("error", "SELF_DEPENDENCY", f"{task.task_id} depends on itself.", f"{config['state_dir']}/tasks"))

    for cycle in _dependency_cycles(state):
        diagnostics.append(Diagnostic("error", "DEPENDENCY_CYCLE", " -> ".join(cycle), f"{config['state_dir']}/tasks"))

    for message in state.messages:
        if message.task_id and message.task_id not in state.tasks:
            diagnostics.append(Diagnostic("error", "MISSING_MESSAGE_TASK", f"{message.message_id} references missing task {message.task_id}.", f"{config['state_dir']}/messages"))
    for handoff in state.handoffs.values():
        if handoff.task_id not in state.tasks:
            diagnostics.append(Diagnostic("error", "MISSING_HANDOFF_TASK", f"{handoff.handoff_id} references missing task {handoff.task_id}.", f"{config['state_dir']}/handoffs"))
    for decision in state.decisions.values():
        if decision.supersedes and decision.supersedes not in state.decisions:
            diagnostics.append(Diagnostic("error", "MISSING_SUPERSEDED_DECISION", f"{decision.decision_id} supersedes missing decision {decision.supersedes}.", f"{config['state_dir']}/decisions"))

    for report in state.reports:
        if report.task_id and report.task_id not in state.tasks:
            diagnostics.append(Diagnostic("error", "MISSING_REPORT_TASK", f"{report.report_id} references missing task {report.task_id}.", f"{config['state_dir']}/reports"))
        if report.goal_id and report.goal_id not in state.goals:
            diagnostics.append(Diagnostic("error", "MISSING_REPORT_GOAL", f"{report.report_id} references missing goal {report.goal_id}.", f"{config['state_dir']}/reports"))
        if report.kind == "goal-review" and report.agent_id != "independent-reviewer":
            diagnostics.append(Diagnostic("error", "INVALID_GOAL_REVIEWER", f"{report.report_id} goal-review must be written by independent-reviewer.", f"{config['state_dir']}/reports"))

    current_review_hash = review_tree_hash(root)

    scope_required_statuses = {"review_ready", "review_failed", "approved", "integrated", "closed"}
    handoff_task_ids = {handoff.task_id for handoff in state.handoffs.values()}
    for task in state.tasks.values():
        if not task.source_write:
            continue
        if task.status not in scope_required_statuses and task.task_id not in handoff_task_ids:
            continue
        try:
            snapshot = load_scope_snapshot(root, config["state_dir"], task.task_id)
        except ScopeError as exc:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "SCOPE_CHECK_REQUIRED",
                    f"{task.task_id} requires a passing scope-check before handoff or review: {exc}.",
                    f"{config['state_dir']}/snapshots",
                )
            )
            continue
        expected_contract = {
            "task_id": task.task_id,
            "writing_lease": task.writing_lease,
            "write_set": list(task.write_set),
            "review_level": task.review_level,
        }
        actual_contract = {key: snapshot.get(key) for key in expected_contract}
        if actual_contract != expected_contract:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "SCOPE_SNAPSHOT_TASK_MISMATCH",
                    f"{task.task_id} scope snapshot does not match its current lease, write_set, or review_level.",
                    f"{config['state_dir']}/snapshots",
                )
            )
            continue
        last_result = snapshot.get("last_result")
        if not isinstance(last_result, Mapping):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "SCOPE_CHECK_REQUIRED",
                    f"{task.task_id} has no persisted scope-check result.",
                    f"{config['state_dir']}/snapshots",
                )
            )
            continue
        if last_result.get("allowed") is not True:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "SCOPE_CHECK_FAILED",
                    f"{task.task_id} has a failing persisted scope-check result.",
                    f"{config['state_dir']}/snapshots",
                )
            )
            continue
        if task.status != "closed" and last_result.get("checked_tree_hash") != current_review_hash:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "SCOPE_CHECK_STALE",
                    f"{task.task_id} scope-check does not match the current reviewable tree.",
                    f"{config['state_dir']}/snapshots",
                )
            )

    for task in state.tasks.values():
        if task.status not in {"approved", "integrated", "closed"}:
            continue
        target_hash = task.review_tree_hash
        if target_hash is None:
            diagnostics.append(Diagnostic("error", "MISSING_TASK_REVIEW_HASH", f"{task.task_id} must bind completion review to review_tree_hash.", f"{config['state_dir']}/tasks"))
            continue
        if task.status in {"approved", "integrated"} and target_hash != current_review_hash:
            diagnostics.append(Diagnostic("error", "TASK_REVIEW_TREE_STALE", f"{task.task_id} is {task.status} for {target_hash}, but the current review tree is {current_review_hash}.", f"{config['state_dir']}/tasks"))

        task_reports = [report for report in state.reports if report.task_id == task.task_id and report.status == "pass"]
        independent = [
            report for report in task_reports
            if report.kind == "independent-review"
            and report.agent_id == "independent-reviewer"
            and report.review_proof is not None
        ]
        matching_independent = [report for report in independent if report.review_proof.reviewed_tree_hash == target_hash]
        if independent and not matching_independent:
            diagnostics.append(Diagnostic("error", "REVIEW_TREE_HASH_MISMATCH", f"Independent review for {task.task_id} does not match task review_tree_hash {target_hash}.", f"{config['state_dir']}/reports"))
        if not matching_independent:
            diagnostics.append(Diagnostic("error", "MISSING_INDEPENDENT_REVIEW", f"{task.task_id} requires a passing fresh-context read-only independent review for {target_hash}.", f"{config['state_dir']}/reports"))
        if task.review_level == "high-risk":
            adversarial = [
                report for report in task_reports
                if report.kind == "adversarial-review"
                and report.agent_id == "independent-reviewer"
                and report.review_proof is not None
                and report.review_proof.reviewed_tree_hash == target_hash
            ]
            if not adversarial:
                diagnostics.append(Diagnostic("error", "MISSING_ADVERSARIAL_REVIEW", f"High-risk task {task.task_id} requires a second independent adversarial review for {target_hash}.", f"{config['state_dir']}/reports"))

    active_writers = [
        task for task in state.tasks.values()
        if task.status == "in_progress" and task.source_write
    ]
    distinct_leases = {task.writing_lease for task in active_writers}
    if len(active_writers) > config["max_concurrent_source_writers"]:
        diagnostics.append(
            Diagnostic(
                "error",
                "TOO_MANY_SOURCE_WRITERS",
                f"{len(active_writers)} source-writing tasks are in progress; maximum is {config['max_concurrent_source_writers']}.",
                f"{config['state_dir']}/tasks",
            )
        )
    if len(distinct_leases) != len(active_writers):
        diagnostics.append(Diagnostic("error", "DUPLICATE_WRITING_LEASE", "Concurrent source-writing tasks must use distinct writing leases.", f"{config['state_dir']}/tasks"))

    concurrent = [task for task in state.tasks.values() if task.status in _ACTIVE_EXECUTION_STATUSES]
    for index, first in enumerate(concurrent):
        for second in concurrent[index + 1:]:
            assessment = assess_parallel_safety(first, second, state.tasks)
            dangerous_codes = {
                "WRITE_WRITE_CONFLICT",
                "WRITE_READ_CONFLICT",
                "CORE_IMPACT_CONFLICT",
                "LEASE_CONFLICT",
            }
            overlapping = [code for code in assessment.reason_codes if code in dangerous_codes]
            if overlapping and first.status == "in_progress" and second.status == "in_progress":
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "ACTIVE_SCOPE_CONFLICT",
                        f"{first.task_id} and {second.task_id} are both in progress: {', '.join(overlapping)}.",
                        f"{config['state_dir']}/tasks",
                    )
                )

    core_paths = set(config["core_paths"])
    for task in state.tasks.values():
        inferred_core = (set(task.write_set) | set(task.impact_set)) & core_paths
        undeclared = sorted(inferred_core - set(task.core_impact_set))
        if undeclared:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "UNDECLARED_CORE_IMPACT",
                    f"{task.task_id} affects configured core path(s) without declaring core_impact_set: {', '.join(undeclared)}.",
                    f"{config['state_dir']}/tasks",
                )
            )

    graph = build_project_graph(root, state, config)
    for invalid in graph["invalid_json"]:
        diagnostics.append(
            Diagnostic(
                "error",
                "INVALID_JSON",
                f"Invalid JSON at line {invalid['line']}, column {invalid['column']}: {invalid['reason']}.",
                str(invalid["source"]),
            )
        )

    for broken in graph["broken_links"]:
        diagnostics.append(
            Diagnostic(
                "error",
                "BROKEN_LINK",
                f"Local Markdown link target {broken['target']!r} is {broken['reason']}.",
                broken["source"],
            )
        )

    diagnostics.extend(_validate_schema_files(root))
    diagnostics.extend(
        Diagnostic(issue.severity, issue.code, issue.message, issue.path)
        for issue in validate_skills(root)
    )

    policy_path = root / config["model_policy_file"]
    if model_policy_required or policy_path.exists():
        if not policy_path.exists():
            diagnostics.append(Diagnostic("error", "MODEL_POLICY_MISSING", "Model policy file is required.", config["model_policy_file"]))
        else:
            try:
                policy = load_model_policy(policy_path)
                if policy.max_concurrent_source_writers != config["max_concurrent_source_writers"]:
                    diagnostics.append(
                        Diagnostic(
                            "error",
                            "ENGINE_WRITER_LIMIT_MISMATCH",
                            "Model policy and Cogem config define different source-writer limits.",
                            config["model_policy_file"],
                        )
                    )
                for task in state.tasks.values():
                    role = policy.roles.get(task.owner)
                    if role is None:
                        diagnostics.append(
                            Diagnostic(
                                "error",
                                "UNKNOWN_TASK_OWNER",
                                f"{task.task_id} is assigned to role {task.owner!r}, which is absent from the engine policy.",
                                f"{config['state_dir']}/tasks",
                            )
                        )
                    elif task.source_write and role.permissions != "scoped-write":
                        diagnostics.append(
                            Diagnostic(
                                "error",
                                "ROLE_SOURCE_WRITE_NOT_ALLOWED",
                                f"{task.task_id} grants source writes to {task.owner}, whose permission class is {role.permissions!r}.",
                                f"{config['state_dir']}/tasks",
                            )
                        )
                if require_engines:
                    resolve_role_engines(policy)
            except ModelPolicyError as exc:
                diagnostics.append(Diagnostic("error", "MODEL_POLICY_ERROR", str(exc), config["model_policy_file"]))

    return sorted(diagnostics, key=lambda item: (item.severity != "error", item.code, item.path or "", item.message))
