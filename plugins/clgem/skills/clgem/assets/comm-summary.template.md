# clgem Project Summary (Leader-maintained rollup)

<!-- Leader Claude is the sole writer. Updated at the end of each loop iteration
     and whenever the Decision Log in Comm.md exceeds 5 entries.
     This file is the FIRST thing Leader reads on session resume. -->

Workspace: <absolute path of the project>
Last updated: <YYYY-MM-DD HH:MM TZ> by Leader at loop iteration <N>

## Project Goal (condensed)

<One paragraph: the essential goal, acceptance criteria in brief, definition of done.
Keep under 10 lines. Full /goal block remains in Comm.md.>

## Completed Work

<!-- One line per done task. Full reports in comm-reports/. -->

- T1 (<YYYY-MM-DD HH:MM TZ>): <what was delivered> → [T1.md](comm-reports/T1.md)

## Architectural Decisions (full rationale)

<!-- Full rationale for each key decision. Entries move here from Comm.md Decision Log
     when the Log exceeds 5 entries. -->

<!-- Heading is the bare id (### D1) so the anchor is a clean `#d1`. Put the title in
     the Title field below — keep links elsewhere as `comm-summary.md#d1` (lowercase). -->

### D1

- **Title**: <decision title>
- **Date**: <YYYY-MM-DD HH:MM TZ>
- **Decision**: <what was decided>
- **Rationale**: <why — constraints, tradeoffs, alternatives rejected>
- **Impact**: <tasks or files affected>

## Antigravity Reviews (full archive)

<!-- When a task reaches done, its full agy review (verdict + complete findings +
     Leader's decision rationale) is moved here INTACT from Comm.md — never condensed.
     comm-index.md keeps only a one-line pointer (id + verdict) back to here.

     BLOAT GUARD: If this section grows excessively large, the OLDEST fully-resolved
     reviews (no open SUPPLEMENT work) may be condensed to "verdict + 2-3 line
     key-findings summary" here, with the full text moved to comm-reports/reviews/R<id>.md
     and a one-line pointer left in its place (e.g., "→ full text: comm-reports/reviews/R1.md").
     The MOST RECENT reviews and any review with an in-progress SUPPLEMENT always keep
     their full text here — never condense active or recent reviews.

     On resume: read this section only when you need a specific past review finding;
     do NOT load the full archive by default. -->

### R1 — review of T1 (agy / Gemini 3.1 Pro (High))

- **Date**: <YYYY-MM-DD HH:MM TZ>
- **VERDICT**: <PASS | CONDITIONAL | FAIL>
- **FINDINGS** (complete, most severe first):
  1. <finding, in full>
- **Leader decision**: <REDO / SUPPLEMENT / ACCEPT> — <full rationale>

## Known Risks & Deferred Items

<!-- Risks flagged by Antigravity reviews, items deferred from Open Items, stall events. -->

- <YYYY-MM-DD HH:MM TZ> RISK: <description>
- <YYYY-MM-DD HH:MM TZ> DEFERRED: <description> (reason: <why deferred>)

## Session Resume Checklist

<!-- Minimum reading order when resuming a session. Do NOT read more than needed. -->

Recommended resume reading order:
1. **This file (comm-summary.md) — top sections first**: Project Goal, Completed Work,
   Architectural Decisions, Known Risks, Session Resume Checklist, Leader Profile.
   Read `## Antigravity Reviews` **only if** you need a specific past review finding —
   do not load the full archive by default.
2. **Comm.md — Status Summary only** (3 lines + "Next action" pointer).
3. **Comm.md — Task Board** (current loop tasks).
4. If `## Interrupted State` exists in Comm.md: read it and act on "Next action on resume".
5. If any task is `in-progress` or `done-pending-review`: read the corresponding
   `comm-reports/T<id>.md` for context before proceeding. If that file does not exist
   yet, read the matching `### T<id>` block in `## Worker Reports` in Comm.md instead.
6. If a past decision is needed: search **comm-index.md** for the decision line,
   then read the linked section in this file.

**Full Comm.md top-to-bottom reading is for audits only — not routine resume.**

## Leader Profile

<!-- This section records the judgment principles, recurring decisions, and user-agreed
     constraints that define how Leader Claude operates on THIS project specifically.
     Update when a new pattern is established or the user explicitly agrees to a constraint.
     Carry this forward if the Leader model is ever swapped (Fable 5 → Opus 4.8).
     This is also the durable home for the DM ledger (Comm.md `## Directives & Memory`):
     when a directive is superseded or the project finishes, move its full rationale here
     (keep the U-id) so the standing constraints/design elements survive past the active table. -->

### Judgment principles adopted on this project

- <e.g., "Always run Scout before any Implementer task involving unfamiliar modules.">

### Recurring decision patterns

- <e.g., "Prefer additive changes over rewrites; flag rewrites to user before spawning.">

### User-agreed constraints & superseded directives (from the DM ledger)

<!-- Active directives live in Comm.md `## Directives & Memory`; their rationale and any
     superseded/closed ones land here, keyed by U-id, so nothing is forgotten. -->

- <U1 [MUST] e.g., "Do not modify files outside src/ without explicit user approval." — rationale; status>

### Model swap events

<!-- Record if Leader model changed mid-project so continuity can be traced. -->

- <YYYY-MM-DD HH:MM TZ>: Leader started on <model>. <reason for any swap, if applicable>
