# Cogem Execution Workflow

## Phase 0: Capture the Goal

The Leader turns the user instruction into a persistent Goal before source work:

```bash
python scripts/cogem.py goal-init GOAL-001 \
  --objective "Deliver the requested outcome" \
  --criterion "Observable acceptance condition" \
  --root .
```

The Leader may create coordination records and generated artifacts, but not source changes. Every real Task explicitly declares `review_level`.

## Phase 1: Analyze and decompose

Inspect the codebase and convert the Goal into dependency-aware Tasks. Attach every Task ID to the Goal, then declare owner, exact read/write/impact scopes, dependencies, acceptance commands, unique lease, and risk level. A Task touching `skills/` must be `high-risk`; this is automatically enforced.

## Phase 2: Analyze

```bash
python scripts/cogem.py skill-check --root .
python scripts/cogem.py graph --root .
python scripts/cogem.py validate --root .
```

Inspect the graph, broken references, dependency closure, and core impact.

## Phase 3: Schedule and authorize

```bash
python scripts/cogem.py parallel TASK-001 TASK-002 --root .
python scripts/cogem.py dispatch-check TASK-001 --root .
```

A successful dispatch writes `.agents/snapshots/TASK-001.json`. The baseline cannot be silently replaced by changing scope or lease. Parallel Workers should operate in isolated worktrees.

## Phase 4: Launch and execute

After authorization, the Leader uses the host runtime's delegation tool to launch the assigned Worker with the Goal, Task contract, graph context, acceptance commands, and stop conditions. A Task record is not a substitute for a Worker session.

Workers modify only `write_set`, record progress, and stop on scope expansion. The Leader continues dispatching runnable work while capacity exists and monitors running Workers instead of ending the turn after planning. New Skills may be scaffolded with `skill-init`; all Skill files remain manifest-controlled.

## Phase 5: Scope verification and handoff

Before any handoff or review transition:

```bash
python scripts/cogem.py scope-check TASK-001 --root .
```

The command compares the current tree to the dispatch baseline, detects created/modified/deleted paths, verifies `write_set`, enforces Skill risk, and requires a same-Task manifest update for Skill content changes. Cogem persists the result. `validate` rejects handoff or review states without passing evidence.

## Phase 6: Integrate and Task-review

Integrate in dependency order, refresh graph and `Comm.md`, record `review_tree_hash`, then launch a fresh read-only Antigravity independent review. Repairs become new Tasks.

## Phase 7: High-risk adversarial pass

High-risk work launches a second fresh Antigravity session using prompt mode `adversarial`, pass index `2`, and no prior findings. Both reviews target the same Task-bound hash.

## Phase 8: Verify and Goal-review

Evaluate every Goal criterion with concrete evidence, then launch a fresh independent Goal review against the current review-tree hash. Any failed criterion or review finding becomes `current_gaps`, increments the repair loop, and produces new or reopened Tasks.

```bash
python scripts/cogem.py goal-check GOAL-001 --root .
```

The Leader follows the returned action:

- `decompose`, `execute`, or `repair`: continue delegating work;
- `verify`: collect missing criterion evidence;
- `review`: run or refresh independent Goal review;
- `ready_to_close`: set the Goal to `achieved`, then check again;
- `complete`: yield the final result;
- `blocked` or `invalid`: report the recorded blocker without claiming completion.

## Phase 9: Release

Run tests, compile checks, Skill policy, graph generation, validation, and the Goal completion gate. Remove live Goal, Task, snapshot, handoff, message, decision, report, and graph artifacts before creating the portable ZIP; then verify the ZIP in a fresh extraction.
