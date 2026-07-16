"""Load and aggregate Cogem's JSON source-of-truth records."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Callable, TypeVar

from .contracts import (
    AgentMessage,
    ContractError,
    DecisionRecord,
    GoalRecord,
    HandoffRecord,
    ReportRecord,
    TaskRecord,
)


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class CogemState:
    tasks: dict[str, TaskRecord]
    decisions: dict[str, DecisionRecord]
    handoffs: dict[str, HandoffRecord]
    messages: tuple[AgentMessage, ...]
    reports: tuple[ReportRecord, ...]
    goals: dict[str, GoalRecord] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> "CogemState":
        return cls(tasks={}, decisions={}, handoffs={}, messages=(), reports=(), goals={})


def _read_records(directory: Path, parser: Callable[[dict], T]) -> list[T]:
    if not directory.exists():
        return []
    records: list[T] = []
    for path in sorted(directory.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ContractError(f"invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
        try:
            records.append(parser(raw))
        except ContractError as exc:
            raise ContractError(f"{path}: {exc}") from exc
    return records


def _index_unique(records: list[T], key_name: str) -> dict[str, T]:
    indexed: dict[str, T] = {}
    for record in records:
        key = getattr(record, key_name)
        if key in indexed:
            raise ContractError(f"duplicate {key_name}: {key}")
        indexed[key] = record
    return indexed


def load_state(root: Path, state_dir: str = ".agents") -> CogemState:
    base = Path(root) / state_dir
    goals = _read_records(base / "goals", GoalRecord.from_dict)
    tasks = _read_records(base / "tasks", TaskRecord.from_dict)
    decisions = _read_records(base / "decisions", DecisionRecord.from_dict)
    handoffs = _read_records(base / "handoffs", HandoffRecord.from_dict)
    messages = _read_records(base / "messages", AgentMessage.from_dict)
    reports = _read_records(base / "reports", ReportRecord.from_dict)

    goal_map = _index_unique(goals, "goal_id")
    task_map = _index_unique(tasks, "task_id")
    decision_map = _index_unique(decisions, "decision_id")
    handoff_map = _index_unique(handoffs, "handoff_id")
    _index_unique(messages, "message_id")
    _index_unique(reports, "report_id")

    return CogemState(
        tasks=dict(sorted(task_map.items())),
        decisions=dict(sorted(decision_map.items())),
        handoffs=dict(sorted(handoff_map.items())),
        messages=tuple(sorted(messages, key=lambda item: (item.created_at, item.message_id))),
        reports=tuple(sorted(reports, key=lambda item: (item.created_at, item.report_id))),
        goals=dict(sorted(goal_map.items())),
    )
