# Comm.md

> Cogem 5.0 portable-distribution bootstrap snapshot.
> After bootstrap, the persistent Leader regenerates this dashboard with `cogem sync` or `cogem all`.
> Edit only the Operator Notes block after generation.

## Current Objective

Capture the user instruction as a Goal, decompose it into scoped Tasks, launch Workers, and continue through verification and review until `goal-check` returns `complete`.

## Current Phase

`bootstrap`

## Authorization Status

- Worker dispatch: **Not authorized**
- Dispatch baseline: **Not recorded**
- Scope verification: **Not run**
- Goal completion gate: **Not run**
- Leader bootstrap authority: coordination records and generated artifacts only

## Active Agents

No active agents.

## Active Goals

No active Goal. Create one with `cogem goal-init GOAL-NNN --objective ... --criterion ...`.

## Goal Loop

No loop is active. After Goal creation, follow every `goal-check` action until `complete`; Task creation or passing tests alone is not completion.

## Active Tasks

No active Tasks. After Goal analysis, create `.agents/tasks/TASK-NNN.json` from `.agents/templates/task.json` before source work.

## File and Section Ownership

No active source-writing ownership or lease.

## Dependency Order

No Task dependencies are registered.

## Shared Decisions

No live decisions are registered.

## Pending Handoffs

No pending handoffs. Cogem rejects handoff state without passing scope evidence.

## Open Blockers

Goal capture and bootstrap prerequisites are incomplete.

## Validation Status

**Not run.** A passing validation result does not authorize work or complete a Goal.

## Graph Status

**Not generated.** After creating the Goal and first Task, run graph, validation, and dispatch-check.

## Scope Status

**No snapshot and no result.** Successful dispatch creates `.agents/snapshots/TASK-NNN.json`; run `scope-check` before handoff or review.

## Review Status

No review requested. High-risk Tasks require independent and adversarial fresh read-only Antigravity passes; Goal completion additionally requires a matching independent `goal-review`.

## Recent Agent Messages

No messages.

## Operator Notes

<!-- COGEM:OPERATOR_NOTES:START -->

<!-- COGEM:OPERATOR_NOTES:END -->
