"""Non-interactive command-line interface for Cogem."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from .comm import write_comm
from .dispatch import check_dispatch
from .evidence import review_tree_hash
from .config import ConfigError, load_config
from .contracts import ContractError
from .goal import assess_goal, initialize_goal
from .graph import build_project_graph, write_graph_artifacts
from .model_policy import ModelPolicyError, engine_plan, load_model_policy, resolve_role_engines
from .parallel import assess_parallel_safety
from .scope import ScopeError, check_scope
from .state import load_state
from .validation import Diagnostic, validate_project
from .skill_init import initialize_skill, normalize_resources
from .skill_policy import SkillPolicyError, validate_skills


EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_CONFIG = 2
EXIT_BROKEN_LINK = 3
EXIT_DEPENDENCY_CYCLE = 4
EXIT_PARALLEL_UNSAFE = 5
EXIT_DISPATCH_BLOCKED = 6
EXIT_SCOPE_VIOLATION = 7


def _add_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=".", help="Project root (default: current directory).")


def _add_engine_plan_arguments(parser: argparse.ArgumentParser) -> None:
    _add_root(parser)
    parser.add_argument(
        "--require-resolved",
        action="store_true",
        help="Fail unless every non-optional role resolves to a concrete model or managed-agent engine.",
    )
    parser.add_argument(
        "--show-engine-ids",
        "--show-model-ids",
        dest="show_engine_ids",
        action="store_true",
        help="Show resolved engine IDs; no credentials are read or printed.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cogem", description="Coordinate and graph multi-agent project work.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    graph = subparsers.add_parser("graph", help="Generate project graph artifacts.")
    _add_root(graph)

    sync = subparsers.add_parser("sync", help="Regenerate Comm.md from .agents records.")
    _add_root(sync)

    validate = subparsers.add_parser("validate", help="Validate project state and references.")
    _add_root(validate)
    validate.add_argument(
        "--require-engines",
        "--require-models",
        dest="require_engines",
        action="store_true",
        help="Require all non-optional role engines to resolve from the environment.",
    )
    validate.add_argument("--json", action="store_true", help="Emit diagnostics as JSON.")

    parallel = subparsers.add_parser("parallel", help="Assess whether two tasks may run concurrently.")
    parallel.add_argument("task_a")
    parallel.add_argument("task_b")
    _add_root(parallel)

    dispatch = subparsers.add_parser("dispatch-check", help="Verify dispatch and record an immutable scope baseline.")
    dispatch.add_argument("task_id")
    _add_root(dispatch)

    scope_check = subparsers.add_parser("scope-check", help="Compare actual project changes with a task's dispatch snapshot.")
    scope_check.add_argument("task_id")
    _add_root(scope_check)

    goal_init = subparsers.add_parser("goal-init", help="Create a persistent top-level goal from a user objective.")
    goal_init.add_argument("goal_id")
    goal_init.add_argument("--objective", required=True, help="User-requested outcome the leader must achieve.")
    goal_init.add_argument(
        "--criterion",
        action="append",
        required=True,
        help="Observable success criterion; repeat for multiple criteria.",
    )
    _add_root(goal_init)

    goal_check = subparsers.add_parser("goal-check", help="Return the next required action for a goal loop.")
    goal_check.add_argument("goal_id")
    _add_root(goal_check)

    review_hash = subparsers.add_parser("review-hash", help="Print the current reviewable-tree SHA-256 evidence hash.")
    _add_root(review_hash)

    skill_check = subparsers.add_parser("skill-check", help="Validate every skills/* directory and manifest.")
    _add_root(skill_check)
    skill_check.add_argument("--json", action="store_true", help="Emit skill diagnostics as JSON.")

    skill_init = subparsers.add_parser("skill-init", help="Create and validate a strict Codex-compatible Skill.")
    skill_init.add_argument("name")
    skill_init.add_argument(
        "--resources",
        default="",
        help="Comma-separated optional directories: references,scripts,assets,schemas,tests.",
    )
    _add_root(skill_init)

    engines = subparsers.add_parser("engine-plan", help="Show capability-profile engine allocation for Plan A roles.")
    _add_engine_plan_arguments(engines)

    # Compatibility alias for the 0.1 CLI. Output uses engine terminology.
    models = subparsers.add_parser("model-plan", help=argparse.SUPPRESS)
    _add_engine_plan_arguments(models)

    all_command = subparsers.add_parser("all", help="Generate graph and Comm.md, then validate the project.")
    _add_root(all_command)
    all_command.add_argument(
        "--require-engines",
        "--require-models",
        dest="require_engines",
        action="store_true",
        help="Require engine environment mappings during validation.",
    )

    return parser


def _root(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _load(root: Path) -> tuple[dict[str, Any], Any]:
    config = load_config(root)
    state = load_state(root, config["state_dir"])
    return config, state


def _graph_summary(graph: dict[str, Any]) -> dict[str, int]:
    return {
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
        "broken_links": len(graph["broken_links"]),
        "invalid_json": len(graph["invalid_json"]),
        "unsafe_pairs": sum(1 for item in graph["parallel_safety"] if not item["parallel_safe"]),
    }


def _diagnostic_exit(diagnostics: list[Diagnostic]) -> int:
    errors = [item for item in diagnostics if item.severity == "error"]
    if not errors:
        return EXIT_OK
    codes = {item.code for item in errors}
    if "BROKEN_LINK" in codes:
        return EXIT_BROKEN_LINK
    if "DEPENDENCY_CYCLE" in codes:
        return EXIT_DEPENDENCY_CYCLE
    if codes & {"CONFIG_ERROR", "CONTRACT_ERROR", "MODEL_POLICY_ERROR", "MODEL_POLICY_MISSING"}:
        return EXIT_CONFIG
    return EXIT_VALIDATION


def _print_diagnostics(diagnostics: list[Diagnostic], as_json: bool) -> None:
    if as_json:
        print(json.dumps([item.to_dict() for item in diagnostics], indent=2, ensure_ascii=False, sort_keys=True))
        return
    if not diagnostics:
        print("Cogem validation: PASS (0 diagnostics)")
        return
    for item in diagnostics:
        location = f" [{item.path}]" if item.path else ""
        print(f"{item.severity.upper()} {item.code}{location}: {item.message}")
    errors = sum(1 for item in diagnostics if item.severity == "error")
    warnings = sum(1 for item in diagnostics if item.severity == "warning")
    print(f"Cogem validation: {errors} error(s), {warnings} warning(s)")


def command_graph(root: Path) -> int:
    config, state = _load(root)
    graph = build_project_graph(root, state, config)
    write_graph_artifacts(graph, root / config["graph_dir"])
    print(json.dumps(_graph_summary(graph), sort_keys=True))
    return EXIT_OK


def command_sync(root: Path) -> int:
    config, state = _load(root)
    graph = build_project_graph(root, state, config)
    write_comm(
        root / config["comm_file"],
        state,
        objective=config["objective"],
        phase=config["phase"],
        graph_summary=_graph_summary(graph),
        recent_message_limit=config["recent_message_limit"],
    )
    print(config["comm_file"])
    return EXIT_OK


def command_parallel(root: Path, task_a: str, task_b: str) -> int:
    config, state = _load(root)
    missing = [task_id for task_id in (task_a, task_b) if task_id not in state.tasks]
    if missing:
        raise ContractError(f"task(s) not found: {', '.join(missing)}")
    result = assess_parallel_safety(state.tasks[task_a], state.tasks[task_b], state.tasks)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False, sort_keys=True))
    return EXIT_OK if result.parallel_safe else EXIT_PARALLEL_UNSAFE


def command_dispatch_check(root: Path, task_id: str) -> int:
    result = check_dispatch(root, task_id, record_snapshot=True)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False, sort_keys=True))
    return EXIT_OK if result.allowed else EXIT_DISPATCH_BLOCKED


def command_scope_check(root: Path, task_id: str) -> int:
    result = check_scope(root, task_id)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False, sort_keys=True))
    return EXIT_OK if result.allowed else EXIT_SCOPE_VIOLATION


def command_goal_init(root: Path, goal_id: str, objective: str, criteria: Sequence[str]) -> int:
    path = initialize_goal(root, goal_id, objective, criteria)
    payload = {
        "goal": path.relative_to(root).as_posix(),
        "goal_id": goal_id,
        "status": "active",
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    return EXIT_OK


def command_goal_check(root: Path, goal_id: str) -> int:
    result = assess_goal(root, goal_id)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False, sort_keys=True))
    return EXIT_OK


def command_skill_check(root: Path, as_json: bool) -> int:
    issues = validate_skills(root)
    if as_json:
        print(json.dumps([asdict(issue) for issue in issues], indent=2, ensure_ascii=False, sort_keys=True))
    elif not issues:
        print("Cogem skill validation: PASS (0 diagnostics)")
    else:
        for issue in issues:
            print(f"{issue.severity.upper()} {issue.code} [{issue.path}]: {issue.message}")
    return EXIT_OK if not issues else EXIT_VALIDATION


def command_skill_init(root: Path, name: str, resources: str) -> int:
    selected = normalize_resources([resources])
    skill = initialize_skill(root, name, selected)
    payload = {
        "skill": skill.relative_to(root).as_posix(),
        "resources": list(selected),
        "validation": "pass",
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    return EXIT_OK


def command_engine_plan(root: Path, require_resolved: bool, show_engine_ids: bool) -> int:
    config = load_config(root)
    policy = load_model_policy(root / config["model_policy_file"])
    rows = engine_plan(policy)
    if require_resolved:
        resolved = resolve_role_engines(policy)
        if show_engine_ids:
            for row in rows:
                item = resolved.get(row["role"])
                row["engine_id"] = item.engine_id if item else None
    elif show_engine_ids:
        try:
            resolved = resolve_role_engines(policy)
        except ModelPolicyError:
            resolved = {}
        for row in rows:
            item = resolved.get(row["role"])
            row["engine_id"] = item.engine_id if item else None
    print(json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True))
    return EXIT_OK


def command_all(root: Path, require_engines: bool) -> int:
    config, state = _load(root)
    graph = build_project_graph(root, state, config)
    write_graph_artifacts(graph, root / config["graph_dir"])
    write_comm(
        root / config["comm_file"],
        state,
        objective=config["objective"],
        phase=config["phase"],
        graph_summary=_graph_summary(graph),
        recent_message_limit=config["recent_message_limit"],
    )
    diagnostics = validate_project(root, require_engines=require_engines)
    _print_diagnostics(diagnostics, False)
    return _diagnostic_exit(diagnostics)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = _root(args.root)
    try:
        if args.command == "graph":
            return command_graph(root)
        if args.command == "sync":
            return command_sync(root)
        if args.command == "validate":
            diagnostics = validate_project(root, require_engines=args.require_engines)
            _print_diagnostics(diagnostics, args.json)
            return _diagnostic_exit(diagnostics)
        if args.command == "parallel":
            return command_parallel(root, args.task_a, args.task_b)
        if args.command == "dispatch-check":
            return command_dispatch_check(root, args.task_id)
        if args.command == "scope-check":
            return command_scope_check(root, args.task_id)
        if args.command == "goal-init":
            return command_goal_init(root, args.goal_id, args.objective, args.criterion)
        if args.command == "goal-check":
            return command_goal_check(root, args.goal_id)
        if args.command == "review-hash":
            print(review_tree_hash(root))
            return EXIT_OK
        if args.command == "skill-check":
            return command_skill_check(root, args.json)
        if args.command == "skill-init":
            return command_skill_init(root, args.name, args.resources)
        if args.command in {"engine-plan", "model-plan"}:
            return command_engine_plan(root, args.require_resolved, args.show_engine_ids)
        if args.command == "all":
            return command_all(root, args.require_engines)
    except (ConfigError, ContractError, ModelPolicyError, ScopeError, SkillPolicyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_CONFIG
    parser.error(f"unknown command: {args.command}")
    return EXIT_CONFIG
