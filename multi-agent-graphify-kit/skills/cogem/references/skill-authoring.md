# Skill Authoring Gate

Use the project-level [Skill Authoring Policy](../../../docs/skill-authoring.md).

1. Create a Task with explicit `review_level: high-risk`, exact scope, acceptance commands, and unique lease.
2. Run graph, validation, and `dispatch-check` before editing; dispatch records the baseline.
3. Keep the Skill name at 1–63 lowercase hyphenated characters.
4. Use exactly `name` and `description` single-line frontmatter fields.
5. Restrict the root to `SKILL.md`, `manifest.txt`, `agents/`, `assets/`, `references/`, `scripts/`, `schemas/`, and `tests/`.
6. Change `manifest.txt` in the same Task whenever Skill content changes.
7. Run `skill-check` and `scope-check TASK-NNN` before handoff.
8. Obtain independent and adversarial fresh read-only reviews against the same Task hash.
