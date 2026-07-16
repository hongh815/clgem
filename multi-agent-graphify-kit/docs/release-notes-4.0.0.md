# Cogem 4.0.0 Release Notes

## Breaking contract change

`review_level` is now required in every Task JSON. Records that relied on the former implicit `standard` default must be updated.

## Enforced Skill risk

A shared path predicate normalizes POSIX and Windows separators. `dispatch-check` and `validate` emit `SKILL_REVIEW_LEVEL_REQUIRED` when any Task writing at or below `skills/` is not `high-risk`.

## Codex-compatible Skill layout

Skill roots now allow the `agents/` and `assets/` directories. Optional root entries must be directories, names are limited to 63 characters, and frontmatter contains exactly `name` and `description` as single-line scalars. The Cogem Skill now includes `agents/openai.yaml`.

## Actual-change scope evidence

Successful dispatch writes an immutable file-hash baseline under `.agents/snapshots/`. `scope-check` compares the current tree, reports creation/modification/deletion, verifies `write_set`, enforces Skill risk, and requires same-Task manifest changes. Handoff and review states require passing persisted evidence.

## Skill scaffolding

`skill-init` creates `SKILL.md`, `manifest.txt`, and `agents/openai.yaml`, optionally creates resource directories, validates immediately, and rolls back on failure.

## Clean release enforcement

The deterministic packager now rejects live Task, communication, review, handoff, decision, or scope-snapshot JSON instead of relying only on a manual cleanup step.

The direct packaging launcher also normalizes `sys.path`, so `PYTHONPATH=src python scripts/package_kit.py ...` cannot accidentally import the adjacent `scripts/cogem.py` file as the `cogem` package.

## New exit code

Exit code `7` identifies actual-change scope violations.

## Migration

1. Add `review_level` to every existing Task JSON.
2. Generate a fresh graph.
3. Re-run `dispatch-check` to create baselines for active Tasks.
4. Run `scope-check` before any handoff or review transition.
5. Update custom Skill layouts and frontmatter to the 4.0 contract.
