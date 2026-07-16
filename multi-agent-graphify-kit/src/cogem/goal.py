"""Persistent top-level goal state and leader-loop next-action assessment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable

from .config import load_config
from .contracts import ContractError, GoalRecord
from .evidence import review_tree_hash
from .scope import ScopeError, load_scope_snapshot
from .state import load_state


@dataclass(frozen=True, slots=True)
class GoalCheckResult:
    goal_id: str
    next_action: str
    reasons: tuple[str, ...]
    open_task_ids: tuple[str, ...]
    missing_task_ids: tuple[str, ...]
    failed_criteria: tuple[str, ...]
    pending_criteria: tuple[str, ...]
    current_gaps: tuple[str, ...]
    task_evidence_issues: tuple[str, ...]
    reviewed_tree_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "goal_id": self.goal_id,
            "next_action": self.next_action,
            "reasons": list(self.reasons),
            "open_task_ids": list(self.open_task_ids),
            "missing_task_ids": list(self.missing_task_ids),
            "failed_criteria": list(self.failed_criteria),
            "pending_criteria": list(self.pending_criteria),
            "current_gaps": list(self.current_gaps),
            "task_evidence_issues": list(self.task_evidence_issues),
            "reviewed_tree_hash": self.reviewed_tree_hash,
        }


def initialize_goal(
    root: Path,
    goal_id: str,
    objective: str,
    criteria: Iterable[str],
    *,
    timestamp: str | None = None,
) -> Path:
    """Create a structured active goal from a user instruction and success criteria."""

    root = Path(root).resolve()
    values = tuple(value.strip() for value in criteria if value.strip())
    if not values:
        raise ContractError("goal-init requires at least one non-empty criterion")
    now = timestamp or datetime.now(timezone.utc).isoformat()
    payload = {
        "goal_id": goal_id,
        "objective": objective,
        "status": "active",
        "iteration": 1,
        "criteria": [
            {
                "criterion_id": f"CRIT-{index:03d}",
                "description": value,
                "status": "pending",
                "evidence": [],
            }
            for index, value in enumerate(values, start=1)
        ],
        "task_ids": [],
        "current_gaps": [],
        "review_tree_hash": None,
        "blocker": None,
        "created_at": now,
        "updated_at": now,
    }
    record = GoalRecord.from_dict(payload)
    config = load_config(root)
    path = root / config["state_dir"] / "goals" / f"{record.goal_id}.json"
    if path.exists():
        raise ContractError(f"goal already exists: {record.goal_id}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return path


def assess_goal(root: Path, goal_id: str) -> GoalCheckResult:
    """Return the next action the Coordinator must take for a persistent goal loop."""

    root = Path(root).resolve()
    config = load_config(root)
    state = load_state(root, config["state_dir"])
    goal = state.goals.get(goal_id)
    if goal is None:
        raise ContractError(f"goal not found: {goal_id}")

    current_hash = review_tree_hash(root)
    missing_tasks = tuple(task_id for task_id in goal.task_ids if task_id not in state.tasks)
    open_tasks = tuple(
        task_id
        for task_id in goal.task_ids
        if task_id in state.tasks and state.tasks[task_id].status != "closed"
    )
    failed_criteria = tuple(item.criterion_id for item in goal.criteria if item.status == "fail")
    pending_criteria = tuple(
        item.criterion_id
        for item in goal.criteria
        if item.status != "pass" or not item.evidence
    )
    task_evidence_issues: list[str] = []
    task_evidence_failed = False
    for task_id in goal.task_ids:
        task = state.tasks.get(task_id)
        if task is None or task.status != "closed":
            continue
        if task.source_write:
            try:
                snapshot = load_scope_snapshot(root, config["state_dir"], task_id)
            except ScopeError as exc:
                task_evidence_issues.append(f"{task_id} is missing valid scope evidence: {exc}.")
            else:
                expected_contract = {
                    "task_id": task.task_id,
                    "writing_lease": task.writing_lease,
                    "write_set": list(task.write_set),
                    "review_level": task.review_level,
                }
                actual_contract = {key: snapshot.get(key) for key in expected_contract}
                if actual_contract != expected_contract:
                    task_evidence_issues.append(f"{task_id} scope evidence does not match its current contract.")
                    task_evidence_failed = True
                elif not isinstance(snapshot.get("last_result"), dict):
                    task_evidence_issues.append(f"{task_id} has no persisted scope-check result.")
                elif snapshot["last_result"].get("allowed") is not True:
                    task_evidence_issues.append(f"{task_id} has a failing persisted scope-check result.")
                    task_evidence_failed = True

        target_hash = task.review_tree_hash
        if target_hash is None:
            task_evidence_issues.append(f"{task_id} has no review_tree_hash.")
            continue
        task_reports = [
            report
            for report in state.reports
            if report.task_id == task_id
            and report.review_proof is not None
            and report.review_proof.reviewed_tree_hash == target_hash
        ]
        independent_pass = any(
            report.status == "pass"
            and report.kind == "independent-review"
            and report.agent_id == "independent-reviewer"
            for report in task_reports
        )
        if not independent_pass:
            task_evidence_issues.append(f"{task_id} lacks a matching passing independent review.")
            if any(report.status == "fail" and report.kind == "independent-review" for report in task_reports):
                task_evidence_failed = True
        if task.review_level == "high-risk":
            adversarial_pass = any(
                report.status == "pass"
                and report.kind == "adversarial-review"
                and report.agent_id == "independent-reviewer"
                for report in task_reports
            )
            if not adversarial_pass:
                task_evidence_issues.append(f"{task_id} lacks a matching passing adversarial review.")
                if any(report.status == "fail" and report.kind == "adversarial-review" for report in task_reports):
                    task_evidence_failed = True

    bound_goal_reviews = [
        report
        for report in state.reports
        if report.kind == "goal-review"
        and report.goal_id == goal.goal_id
        and report.agent_id == "independent-reviewer"
        and report.review_proof is not None
        and report.review_proof.reviewed_tree_hash == goal.review_tree_hash
    ]
    matching_reviews = [
        report
        for report in bound_goal_reviews
        if report.status == "pass"
    ]
    failed_goal_review = (
        goal.review_tree_hash == current_hash
        and not matching_reviews
        and any(report.status == "fail" for report in bound_goal_reviews)
    )

    reasons: list[str] = []
    if goal.status == "blocked":
        next_action = "blocked"
        reasons.append(goal.blocker or "The goal is marked blocked without a blocker description.")
    elif missing_tasks:
        next_action = "invalid"
        reasons.append(f"Goal references missing task(s): {', '.join(missing_tasks)}.")
    elif not goal.task_ids:
        next_action = "decompose"
        reasons.append("Create scoped work tasks and attach their IDs to the goal.")
    elif failed_criteria or goal.current_gaps or task_evidence_failed or failed_goal_review or any(
        state.tasks[task_id].status in {"blocked", "review_failed"} for task_id in goal.task_ids
    ):
        next_action = "repair"
        reasons.append("Create or revise repair tasks for failed criteria, review findings, or recorded gaps.")
    elif open_tasks:
        next_action = "execute"
        reasons.append("Dispatch or continue the remaining goal tasks.")
    elif pending_criteria:
        next_action = "verify"
        reasons.append("Evaluate every success criterion and record concrete evidence.")
    elif task_evidence_issues:
        next_action = "review"
        reasons.append("Complete missing Task scope or review evidence before final Goal review.")
    elif goal.review_tree_hash != current_hash or not matching_reviews:
        next_action = "review"
        reasons.append("Bind the current review hash and obtain a fresh passing goal-review.")
    elif goal.status == "achieved":
        next_action = "complete"
        reasons.append("The goal contract, criteria evidence, tasks, and final review all pass.")
    else:
        next_action = "ready_to_close"
        reasons.append("Mark the goal achieved, then run goal-check once more before yielding.")

    return GoalCheckResult(
        goal_id=goal.goal_id,
        next_action=next_action,
        reasons=tuple(reasons),
        open_task_ids=open_tasks,
        missing_task_ids=missing_tasks,
        failed_criteria=failed_criteria,
        pending_criteria=pending_criteria,
        current_gaps=goal.current_gaps,
        task_evidence_issues=tuple(task_evidence_issues),
        reviewed_tree_hash=current_hash,
    )
