# Cogem Coordination State

A portable release contains no live Goal, Task, message, decision, handoff, report, or scope snapshot JSON. `.gitkeep` files retain the directories and `templates/` provides complete examples.

- `goals/`: user objectives, measurable success criteria, loop iteration, gaps, and final review binding;
- `tasks/`: Task contracts;
- `messages/`: append-only communication;
- `decisions/`: shared decisions;
- `handoffs/`: transfer records;
- `reports/`: command and review evidence;
- `snapshots/`: immutable dispatch baselines and persisted scope-check results;
- `templates/`: record examples.

The Coordinator converts each user instruction into one active Goal before source work, then creates and dispatches Tasks that advance it. A successful `dispatch-check` creates the Task snapshot. `scope-check` must pass before handoff or review. The Coordinator runs `goal-check` after every execution, verification, or review cycle and continues until it returns `complete` or a genuine external blocker is recorded.
