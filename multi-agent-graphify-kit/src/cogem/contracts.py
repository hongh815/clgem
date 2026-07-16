"""Strict, portable data contracts used by Cogem state files."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
import re
from typing import Any, Iterable, Mapping


class ContractError(ValueError):
    """Raised when a Cogem JSON record violates its contract."""


TASK_STATUSES = (
    "proposed",
    "ready",
    "assigned",
    "in_progress",
    "blocked",
    "review_ready",
    "review_failed",
    "approved",
    "integrated",
    "closed",
)
MESSAGE_KINDS = ("info", "progress", "question", "answer", "blocker", "review", "handoff")
DECISION_STATUSES = ("proposed", "accepted", "superseded", "rejected")
HANDOFF_STATUSES = ("pending", "accepted", "rejected", "completed")
REPORT_STATUSES = ("pass", "fail", "warn")
REVIEW_LEVELS = ("standard", "high-risk")
REVIEW_PROMPT_MODES = ("independent", "adversarial")
GOAL_STATUSES = ("active", "verifying", "achieved", "blocked")
CRITERION_STATUSES = ("pending", "pass", "fail")

_ID_PATTERNS = {
    "goal_id": re.compile(r"^GOAL-[0-9]{3,}$"),
    "criterion_id": re.compile(r"^CRIT-[0-9]{3,}$"),
    "task_id": re.compile(r"^TASK-[0-9]{3,}$"),
    "message_id": re.compile(r"^MSG-[0-9]{3,}$"),
    "decision_id": re.compile(r"^DEC-[0-9]{3,}$"),
    "handoff_id": re.compile(r"^HANDOFF-[0-9]{3,}$"),
    "report_id": re.compile(r"^REPORT-[0-9]{3,}$"),
}
_AGENT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def _require_mapping(data: Mapping[str, Any] | Any, record_name: str) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise ContractError(f"{record_name} must be a JSON object")
    return data


def _check_unknown(data: Mapping[str, Any], allowed: set[str], record_name: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ContractError(f"{record_name} contains unknown field(s): {', '.join(unknown)}")


def _string(data: Mapping[str, Any], key: str, *, allow_empty: bool = False) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ContractError(f"{key} must be a string")
    value = value.strip()
    if not allow_empty and not value:
        raise ContractError(f"{key} must not be empty")
    return value


def _optional_string(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{key} must be a non-empty string or null")
    return value.strip()


def _boolean(data: Mapping[str, Any], key: str, default: bool) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ContractError(f"{key} must be a boolean")
    return value


def _identifier(data: Mapping[str, Any], key: str) -> str:
    value = _string(data, key)
    pattern = _ID_PATTERNS[key]
    if not pattern.fullmatch(value):
        raise ContractError(f"{key} has invalid format: {value!r}")
    return value


def _agent_id(data: Mapping[str, Any], key: str) -> str:
    value = _string(data, key)
    if not _AGENT_ID.fullmatch(value):
        raise ContractError(f"{key} must use lowercase letters, numbers, and hyphens: {value!r}")
    return value


def _enum(data: Mapping[str, Any], key: str, allowed: Iterable[str]) -> str:
    value = _string(data, key)
    options = tuple(allowed)
    if value not in options:
        raise ContractError(f"{key} must be one of {', '.join(options)}; got {value!r}")
    return value


def _string_tuple(data: Mapping[str, Any], key: str, *, paths: bool = False) -> tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ContractError(f"{key} must be an array of strings")
    normalized: list[str] = []
    for item in value:
        text = item.strip()
        if not text:
            raise ContractError(f"{key} must not contain empty strings")
        normalized.append(_normalize_path(text, key) if paths else text)
    if len(normalized) != len(set(normalized)):
        raise ContractError(f"{key} must not contain duplicates")
    return tuple(normalized)


def _normalize_path(value: str, field: str) -> str:
    value = value.replace("\\", "/")
    path = PurePosixPath(value)
    if path.is_absolute() or value.startswith("/"):
        raise ContractError(f"{field} paths must be project-relative: {value!r}")
    if ".." in path.parts:
        raise ContractError(f"{field} paths must not traverse parents: {value!r}")
    normalized = path.as_posix()
    if normalized in ("", "."):
        raise ContractError(f"{field} contains an invalid path: {value!r}")
    return normalized


def _timestamp(data: Mapping[str, Any], key: str) -> str:
    value = _string(data, key)
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{key} must be an ISO-8601 timestamp: {value!r}") from exc
    return value


@dataclass(frozen=True, slots=True)
class GoalCriterion:
    criterion_id: str
    description: str
    status: str
    evidence: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "GoalCriterion":
        data = _require_mapping(raw, "goal criterion")
        _check_unknown(data, {"criterion_id", "description", "status", "evidence"}, "goal criterion")
        return cls(
            criterion_id=_identifier(data, "criterion_id"),
            description=_string(data, "description"),
            status=_enum(data, "status", CRITERION_STATUSES),
            evidence=_string_tuple(data, "evidence"),
        )


@dataclass(frozen=True, slots=True)
class GoalRecord:
    goal_id: str
    objective: str
    status: str
    iteration: int
    criteria: tuple[GoalCriterion, ...]
    task_ids: tuple[str, ...]
    current_gaps: tuple[str, ...]
    review_tree_hash: str | None
    blocker: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "GoalRecord":
        data = _require_mapping(raw, "goal")
        _check_unknown(
            data,
            {
                "goal_id", "objective", "status", "iteration", "criteria",
                "task_ids", "current_gaps", "review_tree_hash", "blocker",
                "created_at", "updated_at",
            },
            "goal",
        )
        raw_criteria = data.get("criteria")
        if not isinstance(raw_criteria, list) or not raw_criteria:
            raise ContractError("criteria must be a non-empty array")
        criteria = tuple(GoalCriterion.from_dict(item) for item in raw_criteria)
        criterion_ids = [item.criterion_id for item in criteria]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ContractError("criteria must not contain duplicate criterion_id values")
        task_ids = _string_tuple(data, "task_ids")
        for task_id in task_ids:
            if not _ID_PATTERNS["task_id"].fullmatch(task_id):
                raise ContractError(f"task_ids contains invalid task ID: {task_id!r}")
        iteration = data.get("iteration")
        if not isinstance(iteration, int) or isinstance(iteration, bool) or iteration < 1:
            raise ContractError("iteration must be a positive integer")
        review_hash = _optional_string(data, "review_tree_hash")
        if review_hash is not None and not re.fullmatch(r"sha256:[0-9a-f]{64}", review_hash):
            raise ContractError("review_tree_hash must be sha256:<64 lowercase hex characters> or null")
        return cls(
            goal_id=_identifier(data, "goal_id"),
            objective=_string(data, "objective"),
            status=_enum(data, "status", GOAL_STATUSES),
            iteration=iteration,
            criteria=criteria,
            task_ids=task_ids,
            current_gaps=_string_tuple(data, "current_gaps"),
            review_tree_hash=review_hash,
            blocker=_optional_string(data, "blocker"),
            created_at=_timestamp(data, "created_at"),
            updated_at=_timestamp(data, "updated_at"),
        )


@dataclass(frozen=True, slots=True)
class TaskRecord:
    task_id: str
    title: str
    owner: str
    status: str
    read_set: tuple[str, ...]
    write_set: tuple[str, ...]
    impact_set: tuple[str, ...]
    core_impact_set: tuple[str, ...]
    depends_on: tuple[str, ...]
    acceptance_checks: tuple[str, ...]
    writing_lease: str
    review_level: str
    source_write: bool = True
    priority: str = "normal"
    review_tree_hash: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "TaskRecord":
        data = _require_mapping(raw, "task")
        _check_unknown(
            data,
            {
                "task_id", "title", "owner", "status", "read_set", "write_set",
                "impact_set", "core_impact_set", "depends_on", "acceptance_checks",
                "writing_lease", "source_write", "priority", "review_level", "review_tree_hash", "updated_at",
            },
            "task",
        )
        priority = data.get("priority", "normal")
        if priority not in ("low", "normal", "high", "critical"):
            raise ContractError(f"priority must be low, normal, high, or critical; got {priority!r}")
        updated = _optional_string(data, "updated_at")
        if updated is not None:
            _timestamp({"updated_at": updated}, "updated_at")
        review_hash = _optional_string(data, "review_tree_hash")
        if review_hash is not None and not re.fullmatch(r"sha256:[0-9a-f]{64}", review_hash):
            raise ContractError("review_tree_hash must be sha256:<64 lowercase hex characters> or null")
        task_id = _identifier(data, "task_id")
        dependencies = _string_tuple(data, "depends_on")
        for dependency in dependencies:
            if not _ID_PATTERNS["task_id"].fullmatch(dependency):
                raise ContractError(f"depends_on contains invalid task ID: {dependency!r}")
        return cls(
            task_id=task_id,
            title=_string(data, "title"),
            owner=_agent_id(data, "owner"),
            status=_enum(data, "status", TASK_STATUSES),
            read_set=_string_tuple(data, "read_set", paths=True),
            write_set=_string_tuple(data, "write_set", paths=True),
            impact_set=_string_tuple(data, "impact_set", paths=True),
            core_impact_set=_string_tuple(data, "core_impact_set", paths=True),
            depends_on=dependencies,
            acceptance_checks=_string_tuple(data, "acceptance_checks"),
            writing_lease=_string(data, "writing_lease"),
            source_write=_boolean(data, "source_write", True),
            priority=priority,
            review_level=_enum(data, "review_level", REVIEW_LEVELS),
            review_tree_hash=review_hash,
            updated_at=updated,
        )


@dataclass(frozen=True, slots=True)
class AgentMessage:
    message_id: str
    agent_id: str
    task_id: str | None
    kind: str
    body: str
    created_at: str

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "AgentMessage":
        data = _require_mapping(raw, "message")
        _check_unknown(data, {"message_id", "agent_id", "task_id", "kind", "body", "created_at"}, "message")
        task_id = _optional_string(data, "task_id")
        if task_id is not None and not _ID_PATTERNS["task_id"].fullmatch(task_id):
            raise ContractError(f"task_id has invalid format: {task_id!r}")
        return cls(
            message_id=_identifier(data, "message_id"),
            agent_id=_agent_id(data, "agent_id"),
            task_id=task_id,
            kind=_enum(data, "kind", MESSAGE_KINDS),
            body=_string(data, "body"),
            created_at=_timestamp(data, "created_at"),
        )


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    decision_id: str
    title: str
    status: str
    owner: str
    rationale: str
    affected_paths: tuple[str, ...]
    created_at: str
    supersedes: str | None = None

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "DecisionRecord":
        data = _require_mapping(raw, "decision")
        _check_unknown(
            data,
            {"decision_id", "title", "status", "owner", "rationale", "affected_paths", "created_at", "supersedes"},
            "decision",
        )
        supersedes = _optional_string(data, "supersedes")
        if supersedes is not None and not _ID_PATTERNS["decision_id"].fullmatch(supersedes):
            raise ContractError(f"supersedes has invalid decision ID: {supersedes!r}")
        return cls(
            decision_id=_identifier(data, "decision_id"),
            title=_string(data, "title"),
            status=_enum(data, "status", DECISION_STATUSES),
            owner=_agent_id(data, "owner"),
            rationale=_string(data, "rationale"),
            affected_paths=_string_tuple(data, "affected_paths", paths=True),
            created_at=_timestamp(data, "created_at"),
            supersedes=supersedes,
        )


@dataclass(frozen=True, slots=True)
class HandoffRecord:
    handoff_id: str
    from_agent: str
    to_agent: str
    task_id: str
    status: str
    summary: str
    artifacts: tuple[str, ...]
    verification: tuple[str, ...]
    created_at: str

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "HandoffRecord":
        data = _require_mapping(raw, "handoff")
        _check_unknown(
            data,
            {"handoff_id", "from_agent", "to_agent", "task_id", "status", "summary", "artifacts", "verification", "created_at"},
            "handoff",
        )
        task_id = _string(data, "task_id")
        if not _ID_PATTERNS["task_id"].fullmatch(task_id):
            raise ContractError(f"task_id has invalid format: {task_id!r}")
        return cls(
            handoff_id=_identifier(data, "handoff_id"),
            from_agent=_agent_id(data, "from_agent"),
            to_agent=_agent_id(data, "to_agent"),
            task_id=task_id,
            status=_enum(data, "status", HANDOFF_STATUSES),
            summary=_string(data, "summary"),
            artifacts=_string_tuple(data, "artifacts", paths=True),
            verification=_string_tuple(data, "verification"),
            created_at=_timestamp(data, "created_at"),
        )


@dataclass(frozen=True, slots=True)
class ReviewProof:
    engine: str
    session_id: str
    fresh_context: bool
    permissions: str
    source_write_performed: bool
    reviewed_tree_hash: str
    prior_findings_provided: bool
    prompt_mode: str
    pass_index: int

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ReviewProof":
        data = _require_mapping(raw, "review_proof")
        _check_unknown(
            data,
            {
                "engine", "session_id", "fresh_context", "permissions",
                "source_write_performed", "reviewed_tree_hash",
                "prior_findings_provided", "prompt_mode", "pass_index",
            },
            "review_proof",
        )
        required = {
            "engine", "session_id", "fresh_context", "permissions",
            "source_write_performed", "reviewed_tree_hash",
            "prior_findings_provided", "prompt_mode", "pass_index",
        }
        missing = sorted(required - set(data))
        if missing:
            raise ContractError(f"review_proof is missing required field(s): {', '.join(missing)}")
        fresh = _boolean(data, "fresh_context", False)
        if not fresh:
            raise ContractError("review_proof fresh_context must be true")
        permissions = _string(data, "permissions")
        if permissions != "read-only":
            raise ContractError("review_proof permissions must be 'read-only'")
        source_write = _boolean(data, "source_write_performed", False)
        if source_write:
            raise ContractError("review_proof source_write_performed must be false")
        tree_hash = _string(data, "reviewed_tree_hash")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", tree_hash):
            raise ContractError("review_proof reviewed_tree_hash must be sha256:<64 lowercase hex characters>")
        pass_index = data.get("pass_index")
        if not isinstance(pass_index, int) or isinstance(pass_index, bool) or pass_index not in (1, 2):
            raise ContractError("review_proof pass_index must be 1 or 2")
        return cls(
            engine=_string(data, "engine"),
            session_id=_string(data, "session_id"),
            fresh_context=fresh,
            permissions=permissions,
            source_write_performed=source_write,
            reviewed_tree_hash=tree_hash,
            prior_findings_provided=_boolean(data, "prior_findings_provided", False),
            prompt_mode=_enum(data, "prompt_mode", REVIEW_PROMPT_MODES),
            pass_index=pass_index,
        )


@dataclass(frozen=True, slots=True)
class ReportRecord:
    report_id: str
    agent_id: str
    task_id: str | None
    goal_id: str | None
    kind: str
    status: str
    summary: str
    evidence: tuple[str, ...]
    created_at: str
    review_proof: ReviewProof | None = None

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ReportRecord":
        data = _require_mapping(raw, "report")
        _check_unknown(
            data,
            {
                "report_id", "agent_id", "task_id", "goal_id", "kind", "status",
                "summary", "evidence", "created_at", "review_proof",
            },
            "report",
        )
        task_id = _optional_string(data, "task_id")
        if task_id is not None and not _ID_PATTERNS["task_id"].fullmatch(task_id):
            raise ContractError(f"task_id has invalid format: {task_id!r}")
        goal_id = _optional_string(data, "goal_id")
        if goal_id is not None and not _ID_PATTERNS["goal_id"].fullmatch(goal_id):
            raise ContractError(f"goal_id has invalid format: {goal_id!r}")
        kind = _string(data, "kind")
        proof_raw = data.get("review_proof")
        proof = ReviewProof.from_dict(proof_raw) if proof_raw is not None else None
        if kind in {"independent-review", "adversarial-review"}:
            if task_id is None:
                raise ContractError(f"{kind} report requires task_id")
            if proof is None:
                raise ContractError(f"{kind} report requires review_proof")
            if kind == "independent-review" and (proof.prompt_mode != "independent" or proof.pass_index != 1):
                raise ContractError("independent-review requires prompt_mode independent and pass_index 1")
            if kind == "adversarial-review":
                if proof.prompt_mode != "adversarial" or proof.pass_index != 2:
                    raise ContractError("adversarial-review requires prompt_mode adversarial and pass_index 2")
                if proof.prior_findings_provided:
                    raise ContractError("adversarial-review must not receive prior findings")
        if kind == "goal-review":
            if goal_id is None:
                raise ContractError("goal-review report requires goal_id")
            if task_id is not None:
                raise ContractError("goal-review report must not use task_id")
            if proof is None:
                raise ContractError("goal-review report requires review_proof")
            if proof.prompt_mode != "independent" or proof.pass_index != 1:
                raise ContractError("goal-review requires prompt_mode independent and pass_index 1")
            if proof.prior_findings_provided:
                raise ContractError("goal-review must not receive prior findings")
        return cls(
            report_id=_identifier(data, "report_id"),
            agent_id=_agent_id(data, "agent_id"),
            task_id=task_id,
            goal_id=goal_id,
            kind=kind,
            status=_enum(data, "status", REPORT_STATUSES),
            summary=_string(data, "summary"),
            evidence=_string_tuple(data, "evidence"),
            created_at=_timestamp(data, "created_at"),
            review_proof=proof,
        )
