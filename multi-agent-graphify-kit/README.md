# Cogem 5.0 Persistent Multi-Agent Goal Loop

Cogem turns a user instruction into a persistent Goal that a Leader decomposes, delegates to actual Worker sessions, integrates, verifies, and independently reviews until the acceptance criteria are satisfied.

Cogem does not call an LLM provider. The installed Skill instructs the external runtime to keep the Leader active and use its delegation tools; the CLI supplies deterministic Goal, Task, graph, scope, review, and completion gates.

## Plan A topology

| Role | Profile | Configured runtime | Permission boundary |
| --- | --- | --- | --- |
| Persistent Leader / Coordinator | `reasoning-high` | `gpt-5.6-sol` | Goal ownership, delegation, integration, and loop control |
| Graph Analyst | `balanced` | `gpt-5.6-terra` | Generated graph artifacts only |
| Worker A | `balanced` | `gpt-5.6-terra` | Assigned `write_set` only |
| Worker B | `balanced` | `gpt-5.6-terra` | Assigned `write_set` only |
| Independent Reviewer | `review-high` | `antigravity-preview-05-2026` | Fresh-context, read-only review |

At most two source-writing tasks run concurrently. Parallel Workers should use isolated worktrees or equivalent task-isolated filesystems so per-task scope evidence cannot be contaminated by another Worker’s writes.

High-risk work receives a second fresh Antigravity session with an adversarial brief. This is a second pass of the same reviewer role, not a sixth permanent role.

## What changed in 5.0

Version 5.0 adds the missing top-level delivery loop:

- `goal-init` captures the user instruction and measurable criteria;
- the Leader must decompose the Goal and launch real Worker sessions through the host runtime;
- `goal-check` returns the next loop action instead of allowing plan-only termination;
- passing tests do not close a Goal while criteria, gaps, Tasks, or review evidence remain;
- Task or Goal review findings trigger another repair iteration;
- a fresh independent `goal-review` must pass against the current review-tree hash;
- generated communication and graphs expose Goal state and Goal-to-Task relationships;
- portable releases reject live Goal records.

See [5.0 release notes](docs/release-notes-5.0.0.md). Version 4.0 scope and Skill safeguards remain active.

## Fresh-distribution state

The portable ZIP contains templates and empty live-state directories, but no active Goal, Task, scope snapshot, review report, or generated `.graph/` output. `Comm.md` explicitly reports bootstrap status. A passing `validate` result alone never means the requested outcome is complete.

## Goal loop and first dispatch

1. Configure `cogem.config.json`.
2. Capture the instruction as a Goal:

```bash
python scripts/cogem.py goal-init GOAL-001 \
  --objective "Deliver the requested outcome" \
  --criterion "Observable acceptance condition" \
  --root .
```

3. Analyze the project and create dependency-aware Task contracts from `.agents/templates/task.json`.
4. Attach Task IDs to the Goal and declare exact scope, dependencies, acceptance commands, `review_level`, and unique writing leases.
5. Run:

```bash
python scripts/cogem.py skill-check --root .
python scripts/cogem.py graph --root .
python scripts/cogem.py validate --root .
python scripts/cogem.py dispatch-check TASK-NNN --root .
```

A successful `dispatch-check` both authorizes the Worker and writes `.agents/snapshots/TASK-NNN.json`. The baseline is not silently replaced if the lease, write scope, or risk level later changes.

The Leader must then use the external runtime's delegation mechanism to launch the Worker. Merely creating `.agents/tasks/TASK-NNN.json` is not execution.

For a proposed parallel pair:

```bash
python scripts/cogem.py parallel TASK-001 TASK-002 --root .
```

After integration, criterion verification, and independent Goal review:

```bash
python scripts/cogem.py goal-check GOAL-001 --root .
```

The Leader follows the returned action and continues. Only `complete` permits a success response; a genuine recorded external blocker permits a blocked response.

## Actual-change gate

Before a Worker writes a handoff or moves a Task to `review_ready`, run:

```bash
python scripts/cogem.py scope-check TASK-NNN --root .
```

The command reports every created, modified, and deleted path. A rename appears as one deletion and one creation. It fails when:

- a changed path falls outside `write_set`;
- a Skill-touching task is not `high-risk`;
- Skill content changed without the corresponding `manifest.txt` changing.

The result is persisted in the Task snapshot and bound to a reviewable-tree hash. Handoff and review states without passing evidence fail `cogem validate`.

## Skill authoring contract

Every Skill lives at `skills/<skill-name>/` and contains:

```text
skills/example-skill/
├── SKILL.md
├── manifest.txt
└── agents/
    └── openai.yaml        # recommended; created by skill-init
```

Optional root directories are:

```text
agents/  assets/  references/  scripts/  schemas/  tests/
```

`SKILL.md` uses exactly:

```yaml
---
name: example-skill
description: Use when concrete activation conditions apply.
---
```

The lightweight parser intentionally supports only single-line scalar frontmatter. `manifest.txt` lists every Skill file, including itself.

Create a Skill non-interactively:

```bash
python scripts/cogem.py skill-init example-skill --root .
python scripts/cogem.py skill-init example-skill \
  --resources references,scripts,assets,schemas,tests \
  --root .
```

`schemes` is accepted as a compatibility alias for `schemas`.

## Main commands

| Command | Purpose |
| --- | --- |
| `cogem goal-init GOAL --objective ... --criterion ...` | Capture a persistent Goal and measurable criteria |
| `cogem goal-check GOAL` | Select the next leader-loop action and enforce completion evidence |
| `cogem skill-init NAME` | Create and immediately validate a strict Skill |
| `cogem skill-check` | Validate all Skill names, frontmatter, layouts, manifests, and schemas |
| `cogem graph` | Generate project graph artifacts and input fingerprint |
| `cogem sync` | Regenerate `Comm.md` while preserving Operator Notes |
| `cogem validate` | Validate contracts, references, risk, scope evidence, reviews, and engine policy |
| `cogem dispatch-check TASK` | Authorize dispatch and record the immutable scope baseline |
| `cogem scope-check TASK` | Compare actual changes with the dispatch baseline |
| `cogem parallel TASK-A TASK-B` | Assess concurrent execution safety |
| `cogem review-hash` | Print the current reviewable-tree hash |
| `cogem engine-plan` | Display role-to-engine allocation |
| `cogem all` | Generate graph and communication artifacts, then validate |

All examples may be run as `python scripts/cogem.py ... --root .`.

### Exit codes

| Code | Meaning |
| ---: | --- |
| `0` | Success, authorized, scope-compliant, or parallel-safe |
| `1` | General validation failure |
| `2` | Configuration, contract, Skill policy, or engine-policy error |
| `3` | Broken local Markdown reference |
| `4` | Task dependency cycle |
| `5` | Unsafe parallel pair |
| `6` | Dispatch blocked |
| `7` | Actual changes violate Task scope |

## Coordination state

```text
.agents/
├── goals/       Persistent objectives, criteria, iterations, gaps, and blockers
├── tasks/       Bounded Worker assignments driven by Goals
├── messages/    Append-only communication
├── decisions/   Shared decisions
├── handoffs/    Producer-to-consumer transfers
├── reports/     Validation and review evidence
├── snapshots/   Dispatch baselines and scope-check results
└── templates/   Complete examples
```

`Comm.md` is a generated operational view. Only its Operator Notes block is manually editable.

## Independent review and completion

Before review, record the current value from:

```bash
python scripts/cogem.py review-hash --root .
```

The external Antigravity reviewer runs in a fresh, read-only session and records `review_proof`. A high-risk Task requires both independent pass 1 and a separate adversarial pass 2 against the same Task-bound hash.

After Task reviews, a `goal-review` report evaluates the integrated outcome against the Goal criteria and current review-tree hash. Failed review findings are recorded as Goal gaps and routed into another Worker repair iteration.

A Goal is complete only when all criteria pass with evidence, every Task is complete, no gap or blocker remains, Goal review passes on the current tree, the Goal is marked `achieved`, and `goal-check` returns `complete`.

## Development and packaging

```bash
python scripts/run_tests.py
python -m compileall -q src scripts skills/cogem/scripts
python scripts/cogem.py skill-check --root .
python scripts/cogem.py validate --root .
python scripts/package_kit.py --root . --output ../multi-agent-graphify-kit-v5.0.0.zip
```

The packager rejects live Goal, Task, message, decision, handoff, report, or scope-snapshot JSON. It also excludes generated graphs, caches, local environments, archives, and secrets. Cogem requires Python 3.11 or later and has no runtime dependency outside the standard library.

## Documentation

- [Architecture](docs/architecture.md)
- [Agent roles](docs/agent-roles.md)
- [Agent model policy](docs/agent-model.md)
- [Execution workflow](docs/execution-workflow.md)
- [Skill Authoring Policy](docs/skill-authoring.md)
- [Parallelization policy](docs/parallelization-policy.md)
- [Validation policy](docs/validation-policy.md)
- [Adoption guide](docs/adoption-guide.md)
- [5.0 release notes](docs/release-notes-5.0.0.md)
- [4.0 release notes](docs/release-notes-4.0.0.md)
