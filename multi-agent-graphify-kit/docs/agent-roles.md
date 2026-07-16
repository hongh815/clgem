# Agent Roles

## Coordinator

Acts as the persistent Leader. It converts the user instruction into one active Goal, defines measurable criteria, decomposes work, launches Worker sessions through the host runtime, monitors runnable work, reviews integration, records new gaps, and continues until `goal-check` returns `complete`.

It owns coordination records, task contracts, decisions, dependency order, leases, integration, `Comm.md`, dispatch authorization, and final state transitions. Bootstrap authority is limited to `.agents/`, `.graph/`, and generated `Comm.md`; it cannot modify project source without a separately assigned Task.

## Graph Analyst

Builds and interprets project graphs, impact relationships, and parallel-safety results. It writes generated artifacts only unless separately assigned a scoped task.

## Worker A and Worker B

Implement disjoint work packages under exact `write_set` boundaries. They receive fresh Goal and Task context in actual delegated sessions, stop on scope expansion, and provide acceptance evidence and handoffs. A JSON assignment without a launched session does not count as execution.

## Independent Reviewer

Runs externally through the configured Antigravity engine in a fresh, read-only session. It reviews the integrated current tree and writes a report with machine-readable `review_proof`. It never repairs source under the review assignment.

High-risk work launches the same role again in a separate fresh adversarial session. The second pass is not a permanent sixth role and does not receive prior findings before forming its own conclusions.

After Task-level review is complete, the same independent role performs a Goal-level review against the active Goal criteria and current review-tree hash. Findings become Goal gaps and trigger another repair iteration; they are not merely reported and ignored.
