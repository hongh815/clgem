# Parallelization Policy

Cogem permits at most two simultaneous source-writing tasks under Plan A. Two tasks may run concurrently only when `cogem parallel` returns exit code `0` and each task separately passes `cogem dispatch-check` immediately before launch.

Each concurrently writing Task must use an isolated worktree or equivalent task-specific checkout. A scope snapshot compares one filesystem tree with one dispatch baseline; unrelated writes in a shared checkout would be attributed to the wrong Task.

## Unsafe relationships

A pair is unsafe when it has any of the following:

- write/write overlap;
- write/read overlap in either direction;
- shared core impact;
- direct or transitive dependency;
- missing declared scope;
- the same writing lease.

`parallel` answers whether a pair is structurally safe together. It does not prove that either task is assigned, that dependencies are complete, or that the graph is current. Those conditions belong to `dispatch-check`.

## Scheduling rule

```text
parallel pair safe
    AND task A dispatch authorized
    AND task B dispatch authorized
        → launch together
otherwise
        → serialize, rescope, or repair state
```

A graph regeneration or task-contract edit invalidates previous dispatch authorization. Run the dispatch gate again immediately before launch. Never point two active scope snapshots at the same writable checkout.
