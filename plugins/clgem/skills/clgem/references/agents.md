# clgem Agent Roster — Roles and Model Assignment

This file replaces the Codex-era `AGENTS.md`. It defines who does what and which
model each role runs on. The guiding principle: **spend Fable-class tokens only on
judgment; spend Haiku-class tokens on everything mechanical.**

## Role table

| Role | Model | Agent type | Responsibility | Activation trigger |
| --- | --- | --- | --- | --- |
| **Leader Claude** | `Fable 5` (the main session — never spawned) | — | Architecture & design, planning, task allocation, verification, all Comm.md writes, final user-facing reporting. | Always. |
| **Implementer** | `sonnet` | general-purpose | Feature implementation, multi-file edits, debugging, writing tests — faithful execution of Leader's design. | Any task that writes non-trivial code. |
| **Scout** | `haiku` | Explore | Codebase reconnaissance, locating files/symbols, summarizing existing behavior. Read-only. | Before planning, or whenever Leader needs facts about the code. |
| **Mechanic** | `haiku` | general-purpose | Mechanical/repetitive edits: renames, formatting, config tweaks, doc updates, applying a pattern Leader already specified exactly. | Bounded tasks with no design judgment. |
| **Fallback Reviewer** | `opus` | general-purpose | Independent critical review — only when the Gemini CLI is unavailable or fails twice. | See references/gemini-review.md. |
| **Gemini Reviewer** | Gemini CLI (external, separate session) | via Bash | Critical verification of every completed task. | After every task completion. |

## Model selection rules (token economy)

- Default workers to **sonnet** for anything involving code judgment; drop to
  **haiku** when the task is fully specified and mechanical. When unsure between
  the two, ask: "could this worker make a wrong design decision?" If no — haiku.
- Never spawn an **opus** worker for implementation. Opus appears only as the
  fallback reviewer, because review quality is the safety net of the whole loop.
- Leader Claude (Fable 5) does not delegate what it can answer in one sentence,
  and does not implement what a sonnet worker can — both directions waste tokens.
- Prefer one well-scoped worker over several overlapping ones; overlapping scopes
  duplicate exploration cost and produce conflicting edits.
- Parallelize only independent tasks. Dependent tasks run sequentially so each
  worker can be given its predecessor's verified output.

## Worker conduct

Workers execute the task as assigned — faithfully, within the stated scope.
A worker that discovers the task is mis-specified reports `STATUS: blocked` with
the reason rather than improvising a different design; design changes are Leader
Claude's call. Workers always end with the REPORT FORMAT block defined in
SKILL.md, because their final message is the only channel back to the Leader and
into Comm.md.
