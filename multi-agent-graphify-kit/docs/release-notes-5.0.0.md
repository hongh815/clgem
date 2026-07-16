# Cogem 5.0.0

Cogem 5.0 turns the Coordinator from a plan generator into a persistent delivery Leader.

## Added

- `.agents/goals/GOAL-*.json` for durable objectives, measurable criteria, iterations, gaps, blockers, and terminal state;
- `cogem goal-init` to capture a user instruction as a Goal;
- `cogem goal-check` to select the next deterministic loop action;
- Goal nodes and `drives` edges in the project graph;
- Goal status and next-loop action in generated `Comm.md`;
- independent `goal-review` evidence tied to the current review-tree hash;
- leader-loop instructions and pressure scenarios that reject plan-only, test-only, and review-only stopping.

## Completion semantics

The Leader may report success only when:

1. every Goal criterion passes with evidence;
2. every referenced Task is complete with required scope and Task-review evidence;
3. no current gap or blocker remains;
4. the independent Goal review passes against the current tree;
5. `goal-check` returns `complete`.

Review findings create another repair iteration. Creating Task records without launching Workers does not count as execution.

## Compatibility

Existing Task, dispatch, scope, graph, Skill, and review contracts remain in place. Goal fields on ordinary reports are optional; `goal-review` reports require a valid Goal reference.
