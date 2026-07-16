# Cogem Architecture

Cogem separates external agent execution from deterministic project governance while preserving one persistent delivery loop.

```text
External runtime
  ├─ Persistent Leader / Coordinator
  ├─ Graph Analyst
  ├─ Worker A / Worker B
  └─ Independent Reviewer
          │
          ▼
user instruction ─ cogem goal-init ───> .agents/goals/GOAL-*.json
goal + tasks ───── host delegation ───> running Worker sessions
.agents/*.json ─── cogem sync ────────> Comm.md
project tree ───── cogem graph ───────> .graph/*
skills/* ───────── cogem skill-check ─> Skill diagnostics
task + graph ───── cogem dispatch-check> authorization + baseline
baseline + tree ── cogem scope-check ─> actual-change evidence
goal + evidence ── cogem goal-check ──> next loop action
all inputs ─────── cogem validate ────> repository diagnostics
```

## Main boundaries

- `.agents/goals/` stores the leader-owned objective, acceptance criteria, iteration, gaps, and terminal status.
- `.agents/tasks/` stores bounded Worker assignments derived from the active Goal.
- `.agents/snapshots/` stores immutable dispatch baselines and scope results.
- `.graph/` is generated analysis state.
- `skills/*/manifest.txt` is authoritative inside each Skill.
- the external runtime owns model sessions, actual delegation, and filesystem permissions.
- Cogem CLI commands persist and validate loop state; a Task record by itself is never evidence that a Worker was launched.

## Persistent loop boundary

The Leader remains responsible from the first instruction through terminal Goal evidence. `goal-check` deterministically selects the next action: decompose, execute, repair, verify, review, ready-to-close, complete, blocked, or invalid.

The runtime may yield only when `goal-check` returns `complete`, or when a genuine external blocker is recorded. Passing tests or finishing the initial Task list does not close a Goal if acceptance criteria, review evidence, or discovered gaps remain unresolved.

## Hash boundaries

The graph fingerprint excludes generated graph data, communication churn, reports, and scope snapshots. Recording dispatch evidence therefore does not immediately stale the graph.

The scope baseline hashes reviewable project files while excluding generated artifacts, secrets, `Comm.md`, and live coordination records. The scope result records the current reviewable-tree hash.

The review hash excludes all `.agents/` state, so evidence records do not alter their own target.

## Concurrency boundary

Path-intersection analysis decides whether Task contracts are theoretically parallel-safe. Actual-change snapshots operate per filesystem tree. Parallel Writers therefore require isolated worktrees or equivalent task-isolated checkouts for attributable scope evidence.

## Determinism

Graph ordering, diagnostics, hashes, manifests, JSON output, and archive ordering are stable for identical inputs. The packager uses a fixed archive timestamp.
