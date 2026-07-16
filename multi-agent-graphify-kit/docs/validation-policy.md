# Validation Policy

Cogem separates five gates:

1. repository validity — `cogem validate`;
2. parallel safety — `cogem parallel`;
3. dispatch authorization and baseline capture — `cogem dispatch-check`;
4. actual-change compliance — `cogem scope-check`;
5. Goal-loop completion — `cogem goal-check`.

## Structural validation

`validate` checks strict Goal and coordination contracts, required `review_level`, dependencies, leases, writer count, active scope conflicts, core impacts, JSON, Markdown links, generic Skill policy, owner permissions, engine policy, scope evidence before handoff/review, Goal references, and review evidence before completion.

A Task writing at or below `skills/` with any risk level other than `high-risk` produces `SKILL_REVIEW_LEVEL_REQUIRED`.

## Dispatch authorization

`dispatch-check` requires assigned/in-progress status, non-empty source scope, unique lease, completed dependencies, authorized owner, fresh graph, and zero project errors. On success it records an immutable dispatch snapshot. Exit code `6` means blocked.

## Scope verification

`scope-check` compares file hashes against the dispatch snapshot. It accounts for creation, modification, deletion, and rename-as-delete-plus-create. It rejects out-of-scope paths, under-classified Skill work, and Skill content changes without a changed `manifest.txt`. Exit code `7` means scope violation.

The result is stored in `.agents/snapshots/TASK-NNN.json` with `checked_tree_hash`. Handoffs and review states require a passing result. Closed historical Tasks retain their recorded evidence after later work changes the repository.

Because file hashes cannot identify which process changed a shared physical checkout, parallel Workers should use isolated worktrees or equivalent task-specific filesystems.

## Skill validation

All immediate `skills/*` directories use the same policy: 1–63 character names, exact two-field single-line frontmatter, allowed root entries, manifest completeness, and valid JSON schemas. Packaging invokes the same checks.

## Review evidence

Independent and adversarial reports require fresh-context, read-only proof, no source write, valid session identity, target hash, prompt mode, pass index, and prior-findings isolation. Cogem validates evidence records but does not create provider sessions.

Goal review additionally requires `kind: goal-review`, an independent-reviewer agent, a matching Goal ID, no Task ID, pass index `1`, independent prompt mode, and a review-tree hash matching the current project state.

## Goal completion

`goal-check` refuses completion while any of the following remains:

- no Task decomposition exists;
- a referenced Task is missing or unfinished;
- a criterion is pending, failed, or lacks evidence;
- `current_gaps` or a blocker remains;
- a Task review failed;
- Goal-level review is missing, failed, or stale;
- the Goal status has not been explicitly advanced to `achieved`.

Passing tests alone therefore cannot terminate the leader loop.

## Non-interactive behavior

Commands never prompt. Machine-readable command results use JSON; fatal command errors use standard error; stable exit codes allow orchestration and CI to stop immediately.

## Release-state gate

`package_kit.py` refuses to create a portable archive while any live JSON exists under `.agents/goals`, `tasks`, `messages`, `decisions`, `handoffs`, `reports`, or `snapshots`. Templates remain distributable; generated `.graph/` output is excluded.
