# Cogem Communication Protocol

`.agents/` is the source of truth. `Comm.md` is a generated view after bootstrap.

## Record classes

- `goals/`: user objective, success criteria, iteration, attached Tasks, current gaps, and final review hash;
- `tasks/`: scope, owner, status, lease, dependencies, acceptance commands, and review level;
- `messages/`: append-only progress, questions, answers, blockers, and review notifications;
- `decisions/`: shared choices and rationale;
- `handoffs/`: artifacts and evidence transferred to a dependent agent;
- `reports/`: deterministic verification and semantic review evidence;
- `snapshots/`: immutable dispatch baselines and persisted actual-change scope results.

IDs are unique within their record class. Agents create a new record instead of overwriting another agent's record.

## Bootstrap

A release contains no live records. The Coordinator first creates a Goal from the user instruction, then creates the first Task records. Bootstrap authority cannot be used to change source files.

## Leader loop

The Goal is the top-level source of truth. Tasks are replaceable work packages for one iteration. A failed criterion or review finding updates `current_gaps`, increments `iteration`, and creates repair Tasks. The Leader runs `goal-check` after each execution or review phase and does not declare completion before it returns `complete`.

## Review reports

`independent-review`, `adversarial-review`, and `goal-review` reports include `review_proof`. The proof records the external engine, session ID, fresh-context status, read-only permissions, no-source-write status, reviewed tree hash, prior-findings isolation, prompt mode, and pass index.

The first pass uses `prompt_mode: independent` and `pass_index: 1`. The second high-risk pass uses `prompt_mode: adversarial`, `pass_index: 2`, and `prior_findings_provided: false`.

A `goal-review` is a fresh independent pass over the integrated outcome. It binds to `goal_id`, uses no `task_id`, and decides whether the Goal criteria are satisfied as a whole.

## Comm.md ownership

Only the Coordinator or `cogem sync` writes generated sections. Operators may edit only the marked Operator Notes block.
