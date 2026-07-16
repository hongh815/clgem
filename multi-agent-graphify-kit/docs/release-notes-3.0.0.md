# Cogem 3.0.0 Release Notes

## Governance hardening

- Added explicit Coordinator bootstrap authority with a strict no-source-write boundary.
- Added `dispatch-check` and exit code `6` so structural validation is not mistaken for work authorization.
- Added dependency-completion, role-permission, lease, and graph-freshness dispatch gates.

## Skill authoring and distribution

- Added the canonical [Skill Authoring Policy](skill-authoring.md).
- Added a generic validator for every `skills/*` directory.
- Enforced directory/frontmatter naming, `Use when` descriptions, allowed root layout, manifests, and schema JSON.
- Made `manifest.txt` authoritative and connected it to archive creation.
- Added `skill-check` CLI support.

## Graph and review integrity

- Added a deterministic graph input fingerprint.
- Added a deterministic reviewable-tree SHA-256 command.
- Added structured `review_proof` to review reports.
- Added task-bound review gates: approved and integrated states require current-tree freshness, while closed historical tasks retain their recorded review hash.
- Added explicit standard and high-risk task review levels.

## Distribution hygiene

- Removed live example tasks, messages, decisions, and reports from the release state.
- Removed stale graph metrics and verification claims from the distributed `Comm.md`.
- Kept `.graph/` excluded from the ZIP so the adopted project generates its own graph.
- Bumped the package and library version from `0.2.0` to `3.0.0`.

## Migration notes

Existing task records remain compatible because `review_level` defaults to `standard`. Existing non-review reports remain compatible. Review reports of kind `independent-review` or `adversarial-review` must now include `review_proof`.

Existing Skill manifests must add `manifest.txt` itself and every currently present Skill file before packaging succeeds.
