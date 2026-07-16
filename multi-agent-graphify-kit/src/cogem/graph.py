"""Project structure, reference, task, and ownership graph generation."""

from __future__ import annotations

import fnmatch
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable, Mapping
from urllib.parse import unquote, urlsplit

from .parallel import assess_parallel_safety
from .evidence import graph_input_fingerprint
from .state import CogemState


_DEFAULT_IGNORES = (
    ".git/**",
    ".venv/**",
    "venv/**",
    "__pycache__/**",
    "**/__pycache__/**",
    "*.pyc",
    "**/*.pyc",
    ".graph/**",
    "*.zip",
)
_MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
_DEFAULT_JSON_REFERENCE_KEYS = {
    "path", "paths", "file", "files", "artifact", "artifacts",
    "affected_paths", "read_set", "write_set", "impact_set", "core_impact_set",
    "state_dir", "graph_dir", "comm_file", "model_policy_file", "core_paths",
}


def _matches_ignore(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(f"{path}/", pattern) for pattern in patterns)


def _relative_files(root: Path, ignore: tuple[str, ...]) -> tuple[list[str], list[str]]:
    directories: set[str] = {"."}
    files: list[str] = []
    for path in sorted(root.rglob("*")):
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if _matches_ignore(relative, ignore):
            continue
        if path.is_symlink():
            continue
        if path.is_dir():
            directories.add(relative)
        elif path.is_file():
            files.append(relative)
            parent = PurePosixPath(relative).parent.as_posix()
            directories.add(parent if parent else ".")
    return sorted(directories), sorted(files)


def _node(node_id: str, node_type: str, label: str, **extra: Any) -> dict[str, Any]:
    value = {"id": node_id, "type": node_type, "label": label}
    value.update(extra)
    return value


def _edge(source: str, target: str, edge_type: str) -> dict[str, str]:
    return {"source": source, "target": target, "type": edge_type}


def _clean_markdown_target(raw: str) -> str | None:
    target = raw.strip()
    angle_wrapped = target.startswith("<") and target.endswith(">")
    if angle_wrapped:
        target = target[1:-1].strip()
    if not angle_wrapped and " " in target and not target.startswith(("http://", "https://")):
        target = target.split(" ", 1)[0]
    split = urlsplit(target)
    if split.scheme or target.startswith(("//", "mailto:", "data:", "javascript:")):
        return None
    if not split.path:
        return None
    return unquote(split.path)


def _resolve_local_target(root: Path, source_relative: str, target: str) -> str | None:
    source_parent = (root / source_relative).parent
    candidate = (source_parent / target).resolve()
    try:
        return candidate.relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def _json_reference_values(value: Any, keys: set[str], current_key: str | None = None) -> list[str]:
    references: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            references.extend(_json_reference_values(child, keys, str(key)))
    elif isinstance(value, list):
        if current_key in keys:
            references.extend(item.strip() for item in value if isinstance(item, str) and item.strip())
        else:
            for child in value:
                references.extend(_json_reference_values(child, keys, current_key))
    elif isinstance(value, str) and current_key in keys and value.strip():
        references.append(value.strip())
    return references


def _project_json_reference(value: str) -> str | None:
    value = value.replace("\\", "/").strip()
    split = urlsplit(value)
    if split.scheme or value.startswith(("//", "mailto:", "data:", "javascript:")):
        return None
    path = unquote(split.path).strip()
    if not path or path.startswith("/") or "\n" in path or "\r" in path:
        return None
    pure = PurePosixPath(path)
    if ".." in pure.parts or any(character in path for character in "*?[]"):
        return None
    normalized = pure.as_posix()
    return None if normalized in ("", ".") else normalized


def build_project_graph(root: Path, state: CogemState, config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    config = config or {}
    configured_ignore = config.get("ignore", [])
    ignore = tuple(dict.fromkeys((*_DEFAULT_IGNORES, *(configured_ignore if isinstance(configured_ignore, list) else []))))
    directories, files = _relative_files(root, ignore)

    nodes: dict[str, dict[str, Any]] = {}
    edges: set[tuple[str, str, str]] = set()
    broken_links: list[dict[str, str]] = []
    invalid_json: list[dict[str, object]] = []

    for directory in directories:
        nodes[f"dir:{directory}"] = _node(f"dir:{directory}", "directory", directory)
    for relative in files:
        path = root / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        nodes[f"file:{relative}"] = _node(f"file:{relative}", "file", relative, sha256_16=digest, size=path.stat().st_size)

    for directory in directories:
        if directory == ".":
            continue
        parent = PurePosixPath(directory).parent.as_posix() or "."
        edges.add((f"dir:{parent}", f"dir:{directory}", "contains"))
    for relative in files:
        parent = PurePosixPath(relative).parent.as_posix() or "."
        edges.add((f"dir:{parent}", f"file:{relative}", "contains"))

    file_set = set(files)
    dir_set = set(directories)
    for relative in files:
        if not relative.lower().endswith((".md", ".markdown")):
            continue
        text = _safe_read(root / relative)
        for match in _MARKDOWN_LINK.finditer(text):
            cleaned = _clean_markdown_target(match.group(1))
            if cleaned is None:
                continue
            target = _resolve_local_target(root, relative, cleaned)
            if target is None:
                broken_links.append({"source": relative, "target": cleaned, "reason": "outside-project"})
                continue
            target_id = None
            if target in file_set:
                target_id = f"file:{target}"
            elif target in dir_set:
                target_id = f"dir:{target}"
            elif target.endswith("/") and target.rstrip("/") in dir_set:
                target_id = f"dir:{target.rstrip('/')}"
            if target_id:
                edges.add((f"file:{relative}", target_id, "links_to"))
            else:
                broken_links.append({"source": relative, "target": target, "reason": "missing"})

    json_reference_keys = set(config.get("json_reference_keys", _DEFAULT_JSON_REFERENCE_KEYS))
    for relative in files:
        if not relative.lower().endswith(".json"):
            continue
        try:
            raw_json = json.loads((root / relative).read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError) as exc:
            invalid_json.append({"source": relative, "line": 0, "column": 0, "reason": str(exc)})
            continue
        except json.JSONDecodeError as exc:
            invalid_json.append({"source": relative, "line": exc.lineno, "column": exc.colno, "reason": exc.msg})
            continue
        for raw_reference in _json_reference_values(raw_json, json_reference_keys):
            reference = _project_json_reference(raw_reference)
            if reference is None:
                continue
            if reference in file_set:
                target_id = f"file:{reference}"
            elif reference in dir_set:
                target_id = f"dir:{reference}"
            else:
                target_id = f"declared:{reference}"
                nodes.setdefault(target_id, _node(target_id, "declared-path", reference, exists=False))
            edges.add((f"file:{relative}", target_id, "references"))

    def path_node(path: str) -> str:
        if path in file_set:
            return f"file:{path}"
        if path in dir_set:
            return f"dir:{path}"
        node_id = f"declared:{path}"
        nodes.setdefault(node_id, _node(node_id, "declared-path", path, exists=False))
        return node_id

    for goal in state.goals.values():
        goal_id = f"goal:{goal.goal_id}"
        passed = sum(1 for criterion in goal.criteria if criterion.status == "pass" and criterion.evidence)
        nodes[goal_id] = _node(
            goal_id,
            "goal",
            f"{goal.goal_id} {goal.objective}",
            status=goal.status,
            iteration=goal.iteration,
            criteria_passed=passed,
            criteria_total=len(goal.criteria),
        )
        for task_reference in goal.task_ids:
            task_id = f"task:{task_reference}"
            nodes.setdefault(
                task_id,
                _node(task_id, "task-reference", task_reference, exists=task_reference in state.tasks),
            )
            edges.add((goal_id, task_id, "drives"))

    for task in state.tasks.values():
        task_id = f"task:{task.task_id}"
        role_id = f"role:{task.owner}"
        nodes[task_id] = _node(task_id, "task", f"{task.task_id} {task.title}", status=task.status)
        nodes.setdefault(role_id, _node(role_id, "role", task.owner))
        edges.add((role_id, task_id, "owns"))
        for dependency in task.depends_on:
            dependency_id = f"task:{dependency}"
            nodes.setdefault(dependency_id, _node(dependency_id, "task-reference", dependency, exists=dependency in state.tasks))
            edges.add((task_id, dependency_id, "depends_on"))
        for path in task.read_set:
            edges.add((task_id, path_node(path), "reads"))
        for path in task.write_set:
            edges.add((task_id, path_node(path), "writes"))
        for path in task.impact_set:
            edges.add((task_id, path_node(path), "impacts"))
        for path in task.core_impact_set:
            edges.add((task_id, path_node(path), "impacts_core"))

    for decision in state.decisions.values():
        decision_id = f"decision:{decision.decision_id}"
        role_id = f"role:{decision.owner}"
        nodes[decision_id] = _node(decision_id, "decision", f"{decision.decision_id} {decision.title}", status=decision.status)
        nodes.setdefault(role_id, _node(role_id, "role", decision.owner))
        edges.add((role_id, decision_id, "owns"))
        for path in decision.affected_paths:
            edges.add((decision_id, path_node(path), "affects"))

    for handoff in state.handoffs.values():
        handoff_id = f"handoff:{handoff.handoff_id}"
        source_role = f"role:{handoff.from_agent}"
        target_role = f"role:{handoff.to_agent}"
        nodes[handoff_id] = _node(handoff_id, "handoff", handoff.handoff_id, status=handoff.status)
        nodes.setdefault(source_role, _node(source_role, "role", handoff.from_agent))
        nodes.setdefault(target_role, _node(target_role, "role", handoff.to_agent))
        edges.add((source_role, handoff_id, "produces"))
        edges.add((handoff_id, target_role, "hands_to"))
        edges.add((handoff_id, f"task:{handoff.task_id}", "for_task"))
        for path in handoff.artifacts:
            edges.add((handoff_id, path_node(path), "transfers"))

    safety: list[dict[str, Any]] = []
    task_values = list(state.tasks.values())
    for index, first in enumerate(task_values):
        for second in task_values[index + 1:]:
            safety.append(assess_parallel_safety(first, second, state.tasks).to_dict())

    node_list = sorted(nodes.values(), key=lambda item: item["id"])
    edge_list = [
        _edge(source, target, edge_type)
        for source, target, edge_type in sorted(edges, key=lambda value: (value[0], value[1], value[2]))
    ]
    return {
        "version": 1,
        "root": ".",
        "input_fingerprint": graph_input_fingerprint(root, files),
        "nodes": node_list,
        "edges": edge_list,
        "broken_links": sorted(broken_links, key=lambda item: (item["source"], item["target"], item["reason"])),
        "invalid_json": sorted(invalid_json, key=lambda item: (str(item["source"]), int(item["line"]), int(item["column"]))),
        "parallel_safety": safety,
    }


def _mermaid_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', "\\\"").replace("\n", " ")


def graph_to_mermaid(graph: Mapping[str, Any]) -> str:
    lines = ["flowchart LR"]
    aliases: dict[str, str] = {}
    for index, node in enumerate(graph.get("nodes", []), start=1):
        alias = f"n{index:04d}"
        aliases[node["id"]] = alias
        label = _mermaid_text(f"{node['type']}: {node['label']}")
        lines.append(f'  {alias}["{label}"]')
    for edge in graph.get("edges", []):
        source = aliases.get(edge["source"])
        target = aliases.get(edge["target"])
        if source and target:
            label = _mermaid_text(edge["type"])
            lines.append(f'  {source} -- "{label}" --> {target}')
    return "\n".join(lines) + "\n"


def graph_report_markdown(graph: Mapping[str, Any]) -> str:
    unsafe = [item for item in graph.get("parallel_safety", []) if not item.get("parallel_safe")]
    lines = [
        "# Cogem Project Graph Report",
        "",
        f"- Input fingerprint: `{graph.get('input_fingerprint', 'missing')}`",
        f"- Nodes: {len(graph.get('nodes', []))}",
        f"- Edges: {len(graph.get('edges', []))}",
        f"- Broken local links: {len(graph.get('broken_links', []))}",
        f"- Invalid JSON files: {len(graph.get('invalid_json', []))}",
        f"- Unsafe task pairs: {len(unsafe)}",
        "",
        "## Broken Local Links",
        "",
    ]
    if graph.get("broken_links"):
        for item in graph["broken_links"]:
            lines.append(f"- `{item['source']}` → `{item['target']}` ({item['reason']})")
    else:
        lines.append("None.")
    lines.extend(["", "## Invalid JSON", ""])
    if graph.get("invalid_json"):
        for item in graph["invalid_json"]:
            lines.append(f"- `{item['source']}` line {item['line']}, column {item['column']}: {item['reason']}")
    else:
        lines.append("None.")
    lines.extend(["", "## Unsafe Task Pairs", ""])
    if unsafe:
        for item in unsafe:
            codes = ", ".join(item["reason_codes"])
            lines.append(f"- `{item['task_a']}` × `{item['task_b']}`: {codes}")
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def write_graph_artifacts(graph: Mapping[str, Any], output_dir: Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "project-graph.json").write_text(json.dumps(graph, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (output / "project-graph.mmd").write_text(graph_to_mermaid(graph), encoding="utf-8")
    (output / "project-graph.md").write_text(graph_report_markdown(graph), encoding="utf-8")
    (output / "parallel-safety-report.json").write_text(
        json.dumps(graph.get("parallel_safety", []), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
