---
name: cogem
description: Use when a user gives a project objective that a leader agent must drive to completion through graph-aware planning, delegated worker execution, verification, independent review, and repeated repair loops without losing scope, decisions, or evidence.
---

# Cogem

## Core behavior

Act as the persistent Leader for the user's objective. Convert the instruction into a structured Goal, dispatch real work to scoped subagents, integrate and review the results, and repeat until the Goal is achieved.

Read and follow [Persistent leader goal loop](references/leader-loop.md) before creating Tasks.

Do not stop after planning, after one implementation pass, or after reporting review findings. Continue through repair iterations. Yield a final completion response only after `cogem goal-check GOAL-NNN` returns `next_action: complete`, or report a genuine external blocker after safe alternatives are exhausted.

## Required topology and execution

Plan A uses Coordinator, Graph Analyst, Worker A, Worker B, and a fresh-context read-only Independent Reviewer. At most two source Writers operate concurrently, preferably in isolated worktrees. High-risk work runs the same reviewer role again in a separate adversarial session.

When the platform exposes subagent or delegation tools, use them. Task contracts are instructions for launched Workers, not substitutes for launching them. The Leader remains responsible for progress and immediately assigns the next runnable work when an agent finishes.

## Start from the user instruction

1. Define one Goal objective and measurable criteria.
2. Run `goal-init` or create the Goal record directly.
3. Analyze the graph and current repository state.
4. Decompose the current gaps into Tasks and attach them to the Goal.
5. Run `goal-check` and follow its required action.

## Before dispatch

1. Create a Task with exact scopes, dependencies, acceptance commands, required `review_level`, and unique lease.
2. Any `write_set` at or below `skills/` must use `high-risk`.
3. Run graph and validation.
4. Run `dispatch-check TASK-NNN`; exit code `0` authorizes work and records the immutable scope baseline.

## During work

Workers modify only `write_set`, record structured messages, and stop on scope expansion. The Leader monitors all active agents, collects handoffs, assigns newly unblocked Tasks, and never leaves a runnable Goal idle.

For new Skills, use `skill-init` when practical. Skill roots allow `agents/`, `assets/`, `references/`, `scripts/`, `schemas/`, and `tests/`; every file remains manifest-controlled.

## Before handoff or review

```bash
python scripts/cogem.py skill-check --root .
python scripts/cogem.py scope-check TASK-NNN --root .
python scripts/cogem.py validate --root .
```

`scope-check` detects created, modified, and deleted paths, rejects writes outside scope, and requires `manifest.txt` to change with Skill content.

## Verification, review, and repair

Close Task-level checks first. Then evaluate every Goal criterion with evidence and run a fresh read-only `goal-review` against the integrated tree. Any unmet criterion or review finding becomes `current_gaps`, increments the Goal iteration, and produces repair Tasks. Repeat execution and review until the final goal review passes.

High-risk Tasks still require their separate adversarial pass.

## References

- [Communication protocol](references/communication-protocol.md)
- [Persistent leader goal loop](references/leader-loop.md)
- [Agent runtime policy](references/agent-model.md)
- [Graph model](references/graph-model.md)
- [Parallel safety](references/parallel-safety.md)
- [Skill authoring gate](references/skill-authoring.md)
- [Command reference](references/commands.md)
