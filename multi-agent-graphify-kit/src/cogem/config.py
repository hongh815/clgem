"""Cogem project configuration loading and normalization."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


class ConfigError(ValueError):
    """Raised when cogem.config.json is malformed."""


DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "objective": "Coordinate multi-agent work with explicit scope and independent review.",
    "phase": "bootstrap",
    "state_dir": ".agents",
    "graph_dir": ".graph",
    "comm_file": "Comm.md",
    "model_policy_file": "agent-models.json",
    "ignore": [],
    "json_reference_keys": [
        "path", "paths", "file", "files", "artifact", "artifacts",
        "affected_paths", "read_set", "write_set", "impact_set", "core_impact_set",
        "state_dir", "graph_dir", "comm_file", "model_policy_file", "core_paths",
    ],
    "core_paths": [
        "AGENTS.md", "Comm.md", "cogem.config.json", "agent-models.json",
        "docs/skill-authoring.md", "skills/cogem/SKILL.md", "skills/cogem/manifest.txt",
        "skills/cogem/schemas/task.schema.json", "skills/cogem/schemas/report.schema.json",
        "src/cogem/contracts.py", "src/cogem/dispatch.py", "src/cogem/skill_policy.py", "src/cogem/validation.py",
    ],
    "max_concurrent_source_writers": 2,
    "recent_message_limit": 20,
}


def _project_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field} must be a non-empty project-relative path")
    normalized = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise ConfigError(f"{field} must be a project-relative path without parent traversal")
    return path.as_posix()


def load_config(root: Path, filename: str = "cogem.config.json") -> dict[str, Any]:
    root = Path(root)
    path = root / filename
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    if not isinstance(raw, Mapping):
        raise ConfigError("cogem.config.json must contain a JSON object")
    unknown = sorted(set(raw) - set(DEFAULT_CONFIG))
    if unknown:
        raise ConfigError(f"unknown configuration field(s): {', '.join(unknown)}")
    config = {**DEFAULT_CONFIG, **raw}
    if config["version"] != 1:
        raise ConfigError("version must be 1")
    for field in ("objective", "phase"):
        if not isinstance(config[field], str) or not config[field].strip():
            raise ConfigError(f"{field} must be a non-empty string")
    for field in ("state_dir", "graph_dir", "comm_file", "model_policy_file"):
        config[field] = _project_path(config[field], field)
    for field in ("ignore", "json_reference_keys", "core_paths"):
        value = config[field]
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
            raise ConfigError(f"{field} must be an array of non-empty strings")
        config[field] = [item.strip().replace("\\", "/") for item in value]
    for field in ("max_concurrent_source_writers", "recent_message_limit"):
        value = config[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ConfigError(f"{field} must be a positive integer")
    return config
