# clgem Agent Roster — Roles and Model Assignment

This file replaces the Codex-era `AGENTS.md`. It defines who does what and which
model each role runs on. The guiding principle: **spend Fable-class tokens only on
judgment; spend Haiku-class tokens on everything mechanical.**

## Role table

| Role | Model | Agent type | Responsibility | Activation trigger |
| --- | --- | --- | --- | --- |
| **Leader Claude** | `Fable 5`, fallback `Opus 4.8` (the main session — never spawned) | — | Architecture & design, planning, task allocation, verification, all Comm.md writes, final user-facing reporting. | Always. |
| **Implementer** | `sonnet` | general-purpose | Feature implementation, multi-file edits, debugging, writing tests — faithful execution of Leader's design. | Any task that writes non-trivial code. |
| **Scout** | `haiku` | Explore | Codebase reconnaissance, locating files/symbols, summarizing existing behavior. Read-only. | Before planning, or whenever Leader needs facts about the code. |
| **Mechanic** | `haiku` | general-purpose | Mechanical/repetitive edits: renames, formatting, config tweaks, doc updates, applying a pattern Leader already specified exactly. | Bounded tasks with no design judgment. |
| **Antigravity Reviewer (default)** | `agy` — Gemini 3.1 Pro (High), captured via `scripts/agy_review.py` (`run_in_background`) | Bash (pywinpty capture) | Independent critical review of every completed task; Leader waits (대기중) until it finishes and the verdict is recorded from the out file. Default because agy capture is verified headless on this setup. | After every task completion. |
| **Fallback Reviewer** | `opus` | general-purpose, `run_in_background: true` | Independent review ONLY when agy capture is unavailable or fails twice; same-vendor (Claude), so independence is weaker. | See [antigravity-review.md](antigravity-review.md) Failure handling. |

## Model selection rules (token economy)

- **Leader model & fallback**: Leader Claude runs on **Fable 5**. If Fable 5 is
  unavailable in the session, the Leader falls back to **Opus 4.8**
  (`claude-opus-4-8`) — never to a worker-tier model (sonnet/haiku), because the
  Leader's judgment is the backbone of the whole loop. Record the active Leader
  model in Comm.md at Step 0.
- Default workers to **sonnet** for anything involving code judgment; drop to
  **haiku** when the task is fully specified and mechanical. When unsure between
  the two, ask: "could this worker make a wrong design decision?" If no — haiku.
- Never spawn an **opus** worker for implementation. Opus appears only as the
  fallback reviewer (used when the Antigravity CLI is unavailable or fails twice),
  because review quality is the safety net of the whole loop.
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

**Connectivity map (graphify).** Building or refreshing the graphify knowledge graph is Tier 0
reconnaissance: the Leader may invoke `/graphify` directly or assign a **general-purpose** worker to
run it (it writes a local `graphify-out/` cache). The read-only **Scout** (Explore) can interpret an
existing graph but cannot write graph files. See
[graphify-integration.md](graphify-integration.md).
