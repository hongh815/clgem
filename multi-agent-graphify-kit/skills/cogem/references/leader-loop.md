# Persistent Leader Goal Loop

Use this procedure whenever a user gives an outcome to deliver.

## Start the goal

1. Translate the instruction into one concrete objective and observable success criteria.
2. Create `.agents/goals/GOAL-NNN.json`, preferably with `cogem goal-init`.
3. Inspect project instructions, the graph, current tests, and affected interfaces before decomposing work.
4. Attach every Task created for the objective to the Goal's `task_ids`.

Do not treat a plan, Task list, or partially passing implementation as goal completion.

## Execute one iteration

1. Identify the gap between the current repository and every pending criterion.
2. Create the smallest dependency-aware Tasks that close those gaps.
3. When the runtime supports subagents, actually launch the Graph Analyst, scoped Workers, and Reviewer. Writing Task JSON without dispatching the assigned agent is not execution.
4. Give each Worker the Goal ID, Task contract, required inputs, acceptance commands, and exact write boundary.
5. Run no more than two source Writers concurrently, and only after the parallel gate passes.
6. Collect handoffs, run acceptance and scope checks, integrate in dependency order, and refresh graph and communication state.

If subagents are unavailable, execute the same roles sequentially while preserving scope and fresh-review separation. Do not silently skip a role.

## Verify and review

After implementation Tasks close:

1. Evaluate every Goal criterion against repository evidence.
2. Mark a criterion `pass` only with concrete evidence. Mark unmet criteria `fail` and copy the gaps to `current_gaps`.
3. If any gap or failed review exists, increment `iteration`, create repair Tasks, and run another execution iteration.
4. When criteria pass, set `status: verifying`, record the current `review_tree_hash`, and launch a fresh read-only `goal-review`.
5. A reviewer finding becomes a recorded gap and a new repair iteration; the Reviewer does not repair source.

## Continue or stop

Run:

```bash
python scripts/cogem.py goal-check GOAL-NNN --root .
```

Obey `next_action`:

- `decompose`: create and attach Tasks.
- `execute`: dispatch or continue Workers.
- `repair`: create repair Tasks and increment the Goal iteration.
- `verify`: evaluate criteria and record evidence.
- `review`: bind the current hash and launch the final goal review.
- `ready_to_close`: mark the Goal `achieved`, then run `goal-check` again.
- `complete`: return the final result to the user.
- `blocked`: return only when the blocker requires unavailable authority, external state, or user input and safe alternatives are exhausted.
- `invalid`: repair coordination state before continuing.

The Leader must not yield a completion response while `next_action` is anything other than `complete`. Status updates are allowed while work continues.
