# Cogem Leader-Driven Agent Operating Instructions

These instructions apply to every agent working in this repository.

## Bootstrap authority

A fresh distribution has no live Goal, Task, scope snapshot, or `.graph/` output. On receiving a user instruction, the Coordinator first creates one Goal with observable success criteria. The Coordinator may create coordination records, generate `.graph/`, regenerate `Comm.md`, and run read-only planning or validation without a Task. Bootstrap authority never permits source, documentation, configuration, schema, script, or Skill changes.

## Persistent Goal loop

The Coordinator is a working Leader, not a planning-only role.

1. Convert the user instruction into `.agents/goals/GOAL-NNN.json`.
2. Inspect the graph and decompose the current Goal gaps into scoped Tasks.
3. Launch the assigned Graph Analyst, Workers, and Reviewer through the runtime's delegation tools when available.
4. Monitor active agents, collect results, integrate, verify criteria, and run review.
5. Convert every failed criterion or review finding into the next repair iteration.
6. Run `python scripts/cogem.py goal-check GOAL-NNN --root .` after every execution or review cycle.

Do not yield a completion response while `goal-check` returns anything other than `complete`. A status update must not pause runnable work. Stop only for `complete` or a genuine external blocker that cannot be resolved within existing authority.

## Mandatory preflight

Before a Worker modifies a file:

1. Read `Comm.md`, the assigned Task, accepted decisions, and relevant graph artifacts.
2. Confirm owner, lease, `read_set`, `write_set`, impacts, dependencies, acceptance commands, and explicit `review_level`.
3. Run `python scripts/cogem.py graph --root .` after contract or structural changes.
4. Run `python scripts/cogem.py validate --root .`.
5. Run `python scripts/cogem.py dispatch-check TASK-NNN --root .` immediately before execution.

Exit code `0` authorizes work and creates an immutable dispatch baseline in `.agents/snapshots/`. A path absent from `write_set` is read-only.

## Skill changes

Every path at or below `skills/` is a critical path. Cogem blocks dispatch and validation unless the Task declares `review_level: high-risk`.

- Follow [Skill Authoring Policy](docs/skill-authoring.md).
- Use `cogem skill-init NAME` for new Skills when practical.
- Keep `manifest.txt` synchronized in the same Task.
- Run `cogem skill-check` and `cogem scope-check TASK-NNN` before handoff.
- Require both independent and adversarial Antigravity review passes.

## Role rules

### Coordinator

- Own the user Goal, criteria, loop iteration, decomposition, dependencies, leases, decisions, integration, and generated `Comm.md`.
- Actually dispatch assigned agents; creating Task records alone is not progress.
- Keep the Goal moving whenever a runnable Task or review exists.
- Permit at most two simultaneous source writers, preferably in isolated worktrees.
- Run `parallel` for each concurrent pair and `dispatch-check` immediately before each Worker starts.
- Reject a handoff or review request without passing scope evidence.
- Convert scope expansion into a revised or new Task; never rebase a baseline after work begins.

### Graph Analyst

- Write only generated graph artifacts unless separately assigned scoped source work.
- Rebuild after structural or Task-contract changes.
- Report broken references, stale inputs, and high-impact nodes without repairing source.

### Worker A and Worker B

- Modify only the assigned `write_set`.
- Stop and report a blocker when work exceeds scope.
- Record structured progress and run every acceptance command.
- Run `scope-check TASK-NNN` before creating a handoff or requesting review.

### Independent Reviewer

- Use the configured Antigravity engine in a fresh, read-only session.
- Review integrated artifacts and command evidence rather than Worker conversation history.
- Bind findings to `review_tree_hash` and complete `review_proof`.
- Do not repair source; repairs become new scoped Tasks.
- For high-risk work, run a second isolated adversarial session without prior findings.
- After all Goal Tasks close and criteria have evidence, run a fresh `goal-review` over the integrated outcome.

## Skill file contract

A Skill root permits only:

```text
SKILL.md  manifest.txt  agents/  assets/  references/  scripts/  schemas/  tests/
```

Names are 1–63 lowercase alphanumeric, hyphen-separated characters. Frontmatter contains exactly `name` and `description` as single-line scalars, and the description starts with `Use when`.

## Completion contract

Before handoff or `review_ready`:

```bash
python scripts/cogem.py scope-check TASK-NNN --root .
```

Then confirm acceptance commands, JSON parsing, Markdown links, Skill policy, and graph freshness. `cogem validate` must find the passing persisted scope result.

Before review, the Coordinator records `cogem review-hash` in Task and Goal `review_tree_hash` fields. Standard Tasks require one matching independent review. High-risk Tasks require a second matching adversarial review. The complete Goal additionally requires a matching fresh `goal-review`.

After Task review:

```bash
python scripts/cogem.py goal-check GOAL-NNN --root .
```

Follow the returned action through further execution, repair, verification, or review. Mark the Goal achieved and return to the user only when a final check returns `complete`.

Final deterministic gate:

```bash
python scripts/run_tests.py
python -m compileall -q src scripts skills/cogem/scripts
python scripts/cogem.py skill-check --root .
python scripts/cogem.py all --root .
```
