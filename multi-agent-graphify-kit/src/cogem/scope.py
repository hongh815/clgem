"""Dispatch-time snapshots and actual-change scope verification."""

from __future__ import annotations

from dataclasses import dataclass
import fnmatch
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

from .config import load_config
from .contracts import ContractError, TaskRecord
from .evidence import review_tree_hash
from .state import load_state
from .task_policy import is_under, skill_review_level_message, task_touches_skill


_SCOPE_IGNORES = (
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
    "Comm.md",
    ".agents/goals/**",
    ".agents/tasks/**",
    ".agents/messages/**",
    ".agents/decisions/**",
    ".agents/handoffs/**",
    ".agents/reports/**",
    ".agents/snapshots/**",
)
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_SNAPSHOT_FIELDS = {
    "version",
    "task_id",
    "writing_lease",
    "write_set",
    "review_level",
    "graph_fingerprint",
    "baseline",
    "last_result",
}
_RESULT_FIELDS = {
    "task_id",
    "allowed",
    "reason_codes",
    "reasons",
    "changes",
    "out_of_scope_paths",
    "missing_manifests",
    "checked_tree_hash",
}


class ScopeError(ValueError):
    """Raised when dispatch scope evidence is missing, unsafe, or inconsistent."""


@dataclass(frozen=True, slots=True)
class ScopeChange:
    path: str
    change_type: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "change_type": self.change_type}


@dataclass(frozen=True, slots=True)
class ScopeCheckResult:
    task_id: str
    allowed: bool
    reason_codes: tuple[str, ...]
    reasons: tuple[str, ...]
    changes: tuple[ScopeChange, ...]
    out_of_scope_paths: tuple[str, ...]
    missing_manifests: tuple[str, ...]
    checked_tree_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "allowed": self.allowed,
            "reason_codes": list(self.reason_codes),
            "reasons": list(self.reasons),
            "changes": [item.to_dict() for item in self.changes],
            "out_of_scope_paths": list(self.out_of_scope_paths),
            "missing_manifests": list(self.missing_manifests),
            "checked_tree_hash": self.checked_tree_hash,
        }


def _matches(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(f"{path}/", pattern) for pattern in patterns)


def _file_hashes(root: Path) -> dict[str, str]:
    root = Path(root).resolve()
    values: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        if _matches(relative, _SCOPE_IGNORES):
            continue
        values[relative] = f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
    return values


def _snapshot_path(root: Path, state_dir: str, task_id: str) -> Path:
    return Path(root) / state_dir / "snapshots" / f"{task_id}.json"


def _snapshot_contract(task: TaskRecord) -> dict[str, object]:
    return {
        "task_id": task.task_id,
        "writing_lease": task.writing_lease,
        "write_set": list(task.write_set),
        "review_level": task.review_level,
    }


def _load_snapshot(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ScopeError(f"scope snapshot is missing: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScopeError(f"scope snapshot is unreadable: {exc}") from exc
    if not isinstance(raw, dict):
        raise ScopeError("scope snapshot must be a JSON object")
    unknown = sorted(set(raw) - _SNAPSHOT_FIELDS)
    if unknown:
        raise ScopeError(f"scope snapshot contains unknown field(s): {', '.join(unknown)}")
    missing = sorted(_SNAPSHOT_FIELDS - set(raw))
    if missing:
        raise ScopeError(f"scope snapshot is missing field(s): {', '.join(missing)}")
    if raw.get("version") != 1:
        raise ScopeError("scope snapshot version must be 1")
    if not isinstance(raw.get("task_id"), str) or not raw["task_id"].strip():
        raise ScopeError("scope snapshot task_id must be a non-empty string")
    if not isinstance(raw.get("writing_lease"), str) or not raw["writing_lease"].strip():
        raise ScopeError("scope snapshot writing_lease must be a non-empty string")
    write_set = raw.get("write_set")
    if not isinstance(write_set, list) or any(not isinstance(value, str) or not value.strip() for value in write_set):
        raise ScopeError("scope snapshot write_set must be an array of non-empty strings")
    if len(write_set) != len(set(write_set)):
        raise ScopeError("scope snapshot write_set must not contain duplicates")
    if raw.get("review_level") not in {"standard", "high-risk"}:
        raise ScopeError("scope snapshot review_level must be standard or high-risk")
    if not isinstance(raw.get("graph_fingerprint"), str) or not _SHA256.fullmatch(raw["graph_fingerprint"]):
        raise ScopeError("scope snapshot graph_fingerprint must be sha256:<64 lowercase hex characters>")
    baseline = raw.get("baseline")
    if not isinstance(baseline, dict) or any(
        not isinstance(key, str) or not key or not isinstance(value, str) or not _SHA256.fullmatch(value)
        for key, value in baseline.items()
    ):
        raise ScopeError("scope snapshot baseline must map non-empty paths to sha256 hashes")
    result = raw.get("last_result")
    if result is not None:
        _validate_result(result, raw["task_id"])
    return raw


def _string_list(value: object, label: str, *, unique: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ScopeError(f"scope snapshot {label} must be an array of non-empty strings")
    if unique and len(value) != len(set(value)):
        raise ScopeError(f"scope snapshot {label} must not contain duplicates")
    return value


def _validate_result(value: object, task_id: str) -> None:
    if not isinstance(value, dict):
        raise ScopeError("scope snapshot last_result must be an object or null")
    unknown = sorted(set(value) - _RESULT_FIELDS)
    if unknown:
        raise ScopeError(f"scope snapshot last_result contains unknown field(s): {', '.join(unknown)}")
    missing = sorted(_RESULT_FIELDS - set(value))
    if missing:
        raise ScopeError(f"scope snapshot last_result is missing field(s): {', '.join(missing)}")
    if value.get("task_id") != task_id:
        raise ScopeError("scope snapshot last_result.task_id must match the snapshot task_id")
    if not isinstance(value.get("allowed"), bool):
        raise ScopeError("scope snapshot last_result.allowed must be a boolean")
    _string_list(value.get("reason_codes"), "last_result.reason_codes", unique=True)
    _string_list(value.get("reasons"), "last_result.reasons")
    _string_list(value.get("out_of_scope_paths"), "last_result.out_of_scope_paths", unique=True)
    _string_list(value.get("missing_manifests"), "last_result.missing_manifests", unique=True)
    changes = value.get("changes")
    if not isinstance(changes, list):
        raise ScopeError("scope snapshot last_result.changes must be an array")
    for item in changes:
        if not isinstance(item, dict) or set(item) != {"path", "change_type"}:
            raise ScopeError("scope snapshot change records must contain exactly path and change_type")
        if not isinstance(item.get("path"), str) or not item["path"].strip():
            raise ScopeError("scope snapshot change path must be a non-empty string")
        if item.get("change_type") not in {"created", "modified", "deleted"}:
            raise ScopeError("scope snapshot change_type must be created, modified, or deleted")
    digest = value.get("checked_tree_hash")
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        raise ScopeError("scope snapshot last_result.checked_tree_hash must be a sha256 hash")


def record_dispatch_snapshot(root: Path, task: TaskRecord, graph_fingerprint: str) -> Path:
    """Create an immutable task baseline, or verify an existing identical baseline."""

    root = Path(root).resolve()
    config = load_config(root)
    path = _snapshot_path(root, config["state_dir"], task.task_id)
    contract = _snapshot_contract(task)
    if path.exists():
        current = _load_snapshot(path)
        existing = {key: current.get(key) for key in contract}
        if existing != contract:
            raise ScopeError("existing scope snapshot does not match the task lease, write_set, or review_level")
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "version": 1,
        **contract,
        "graph_fingerprint": graph_fingerprint,
        "baseline": _file_hashes(root),
        "last_result": None,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _changed_files(baseline: Mapping[str, str], current: Mapping[str, str]) -> tuple[ScopeChange, ...]:
    changes: list[ScopeChange] = []
    for path in sorted(set(baseline) | set(current)):
        if path not in baseline:
            changes.append(ScopeChange(path, "created"))
        elif path not in current:
            changes.append(ScopeChange(path, "deleted"))
        elif baseline[path] != current[path]:
            changes.append(ScopeChange(path, "modified"))
    return tuple(changes)


def _skill_manifest_requirements(changes: tuple[ScopeChange, ...]) -> tuple[str, ...]:
    changed_paths = {item.path for item in changes}
    touched_content: set[str] = set()
    for item in changes:
        normalized = item.path.replace("\\", "/")
        parts = normalized.split("/")
        if len(parts) < 3 or parts[0] != "skills":
            continue
        manifest = f"skills/{parts[1]}/manifest.txt"
        if normalized != manifest:
            touched_content.add(manifest)
    return tuple(sorted(path for path in touched_content if path not in changed_paths))


def check_scope(
    root: Path,
    task_id: str,
    *,
    task: TaskRecord | None = None,
    persist: bool = True,
) -> ScopeCheckResult:
    """Compare the current tree to the dispatch baseline for one task."""

    root = Path(root).resolve()
    config = load_config(root)
    if task is None:
        state = load_state(root, config["state_dir"])
        task = state.tasks.get(task_id)
        if task is None:
            raise ContractError(f"task not found: {task_id}")
    elif task.task_id != task_id:
        raise ScopeError(f"task argument {task.task_id} does not match requested {task_id}")

    path = _snapshot_path(root, config["state_dir"], task_id)
    snapshot = _load_snapshot(path)
    expected = _snapshot_contract(task)
    actual = {key: snapshot.get(key) for key in expected}
    if actual != expected:
        raise ScopeError("scope snapshot does not match the current task contract")

    baseline_raw = snapshot.get("baseline")
    if not isinstance(baseline_raw, dict) or any(not isinstance(key, str) or not isinstance(value, str) for key, value in baseline_raw.items()):
        raise ScopeError("scope snapshot baseline must map paths to hashes")
    current = _file_hashes(root)
    changes = _changed_files(baseline_raw, current)
    out_of_scope = tuple(
        item.path
        for item in changes
        if not any(is_under(item.path, allowed) for allowed in task.write_set)
    )
    missing_manifests = _skill_manifest_requirements(changes)

    findings: list[tuple[str, str]] = []
    if out_of_scope:
        findings.append(("OUT_OF_SCOPE_CHANGE", f"Changed path(s) fall outside write_set: {', '.join(out_of_scope)}."))
    if task_touches_skill(task) and task.review_level != "high-risk":
        findings.append(("SKILL_REVIEW_LEVEL_REQUIRED", skill_review_level_message(task)))
    if missing_manifests:
        findings.append(
            (
                "SKILL_MANIFEST_UPDATE_REQUIRED",
                f"Skill content changed without changing manifest.txt: {', '.join(missing_manifests)}.",
            )
        )

    unique = tuple(dict.fromkeys(findings))
    checked_hash = review_tree_hash(root)
    result = ScopeCheckResult(
        task_id=task_id,
        allowed=not unique,
        reason_codes=tuple(code for code, _ in unique),
        reasons=tuple(message for _, message in unique),
        changes=changes,
        out_of_scope_paths=out_of_scope,
        missing_manifests=missing_manifests,
        checked_tree_hash=checked_hash,
    )
    if persist:
        snapshot["last_result"] = result.to_dict()
        path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return result


def load_scope_snapshot(root: Path, state_dir: str, task_id: str) -> dict[str, Any]:
    """Load a persisted snapshot for validation and orchestration."""

    return _load_snapshot(_snapshot_path(Path(root).resolve(), state_dir, task_id))
