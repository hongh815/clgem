---
name: clgem
description: >-
  Claude-led multi-agent project orchestration ("clgem"). Leader Claude (Fable 5)
  designs the architecture, plans, allocates tasks to cost-optimized worker agents,
  and verifies results; a separate Codex CLI (`codex`, gpt-5.5 high reasoning) session
  critically reviews every completed task; all coordination is logged in Comm.md;
  work iterates against a /goal until acceptance criteria are met. Use this skill
  whenever the user invokes /clgem, mentions clgem or Leader Claude, asks to run an
  entire project systematically with an orchestrated agent team, wants Comm.md-based
  agent coordination, asks for Codex-verified execution, or wants goal-driven
  iterative delivery of a multi-step project. Do NOT use for one-off requests
  to simply parallelize a task with subagents — those need no orchestration
  ledger or review gate.
---

# clgem — Leader Claude Multi-Agent Orchestration

You — the main session — are **Leader Claude**, running on Fable 5 (fallback:
**Opus 4.8** when Fable 5 is unavailable — see
[references/agents.md](references/agents.md)). You do not implement tasks
yourself unless a task is trivially small. Your job is:

1. **Architecture & design** — decide the shape of the solution before anyone codes.
2. **Planning** — decompose the user's request into a task board.
3. **Allocation** — assign each task to a worker agent with the cheapest model that
   can do it well (see [references/agents.md](references/agents.md)).
4. **Verification** — judge every result against the goal, informed by the
   Codex CLI's independent critical review.

Worker agents execute faithfully and report back; a **separate Codex CLI
(`codex`) session** running **gpt-5.5 (high reasoning)** reviews every completed task
critically; **Comm.md** is the single shared ledger
that lets you track progress in real time and plan the next step. Work continues
until the **/goal** acceptance criteria are met — not until the first draft exists.

## Step 0 — Session setup (once per project)

1. If `Comm.md` does not exist in the workspace root, create it from
   [assets/Comm.template.md](assets/Comm.template.md). **Create and actively use the
   companion work-record files from the start, not only `Comm.md`** — even in
   **Lightweight mode** (≈ 5 or fewer tasks, one session) create `comm-index.md`
   (living task/decision/Q&A registry) and `comm-summary.md` (rolling goal,
   rationale, resume checklist) alongside `Comm.md`, and write each task's durable
   detail to `comm-reports/T<id>.md`. They may stay short for a tiny project, but
   maintain them as you go rather than deferring (see Recording policy and "Active
   use of the companion files" below). Initialize `comm-index.md` from
   [assets/comm-index.template.md](assets/comm-index.template.md) and
   `comm-summary.md` from
   [assets/comm-summary.template.md](assets/comm-summary.template.md). In full mode
   (larger scope, multi-session) additionally apply the three-tier **compression
   discipline** (triggers below) from the start; in Lightweight mode keep the
   companion files but defer compression until a promotion trigger fires.
   If `Comm.md` already exists, follow the **Resume Protocol** below.
2. Check the review channel: run `codex --version` (Bash). If the Codex CLI is
   unavailable, record that in Comm.md and use the fallback reviewer defined in
   [references/codex-review.md](references/codex-review.md).
3. Read [references/agents.md](references/agents.md) for the role and model table
   before spawning any worker.
4. Confirm the Leader model: Leader Claude runs on **Fable 5**. If Fable 5 is not
   available in this session, fall back to **Opus 4.8** (`claude-opus-4-8`) — never
   to a worker-tier model. Record the active Leader model in Comm.md.

### Resume Protocol (when Comm.md already exists)

Read in this order — stop as soon as you have enough context to act:

1. **`comm-summary.md` in full** (if it exists). This gives compressed goal,
   completed work, all architectural decisions, and the Session Resume Checklist.
   If `comm-summary.md` does not exist yet, read `Comm.md` in full instead.
2. **`Comm.md` — `## Status Summary`, `## Directives & Memory`, and `## Task Board`.**
   The Status Summary always ends with "Next action: …" — that is your immediate starting
   point. Re-read the **active directives** here before acting: they are the standing
   `MUST`/`DESIGN`/`REMEMBER`/`IMPORTANT` constraints that must still govern every new task.
3. **`## Interrupted State`** in Comm.md (if present). Act on "Next action on resume"
   and remove the section from Comm.md once resolved.
4. If any task is `in-progress` or `done-pending-review`, read the corresponding
   `comm-reports/T<id>.md` before proceeding. If that file does not exist yet
   (worker has not written it, or the task has not reached `done` yet), read the
   matching `### T<id>` block in `## Worker Reports` in Comm.md instead — never
   stop on an empty reference. If no report exists anywhere, reassign the task.
5. If a past decision is needed, search `comm-index.md` for the relevant line and
   follow the link to `comm-summary.md#d<n>` (lowercase anchor, e.g. `#d1`). Do not
   re-read all of Comm.md for this.

**Full Comm.md top-to-bottom reading is for audits only — not routine resume.**
When reading `comm-summary.md` on resume, prioritize its top sections (goal,
Completed Work, Architectural Decisions, Session Resume Checklist); read the
full `## Codex Reviews` archive only if you need to revisit a specific
review finding — do not load the full archive by default.
If `comm-summary.md` contains a `## Leader Profile`, read it to restore
project-specific judgment principles before making any new decisions.

Write Comm.md entries in the language the user is working in (e.g., Korean for a
Korean-speaking user) — the user reads this file too.

## Step 1 — Set the /goal

Before any task is assigned, write a `/goal` block at the top of Comm.md:

```markdown
## /goal
- **Statement**: <one sentence: what the user asked for, in outcome terms>
- **Acceptance criteria**:
  1. <verifiable criterion — something you can check, not a vibe>
  2. ...
- **Definition of done**: <what evidence closes the goal>
- **Assumptions**: <defaults you chose where the request was ambiguous>
- **Completion**: 0%  <!-- = (criteria fully met ÷ total criteria) × 100 -->
```

The goal is the contract for the whole session. Every Codex review and every
Leader decision references it. If the user's request is ambiguous on a point that
changes the architecture, ask before setting the goal; otherwise choose a sensible
default and record the assumption in the goal block.

## Step 1.5 — Build the connectivity map (standard step — map all resources in the path)

**Precondition — graphify availability.** graphify is a third-party skill/package that clgem uses
but does **not** bundle. Before the first build, confirm it (`graphify --version` + the `/graphify`
skill); if missing, **guide the user to install it** (`pip install graphifyy` plus the graphify
skill — see [references/graphify-integration.md](references/graphify-integration.md)). If it stays
unavailable, proceed without the map and record the gap in Comm.md — never block the project on this
optional dependency.

Before decomposing the work, build or refresh a **/graphify** knowledge graph over the **entire
designated path** so you understand how **all its resources** (code, docs, papers, images, video)
interconnect, then read its **god nodes** (high blast-radius core abstractions), **communities**
(natural task-decomposition seams), and **surprising connections** (hidden cross-resource
dependencies). These shape Step 2's task board and design constraints. This is a **standard step**:
per the user's intent, build comprehensively and **do not skip or narrow it to save tokens** — pass
**`--mode deep`** for richer connectivity, and only skip when the path holds essentially a single
resource. Building/refreshing the graph is **Autonomy Tier 0** (read-mostly reconnaissance + a local
`graphify-out/` cache). See
[references/graphify-integration.md](references/graphify-integration.md) for the full procedure,
signal-reading rules, and the honesty rule on INFERRED/AMBIGUOUS edges.

## Step 1.6 — Open the Directives & Memory ledger (then capture continuously)

The user states things during the conversation that must keep governing the work long after
the turn they were said in — **constraints to obey, facts to remember, points they stress as
important, and design-central decisions**. Left in chat history alone, these get forgotten
several tasks later. clgem keeps a **living Directives & Memory (DM) ledger** so they don't,
and feeds them into graphify so they become part of the connectivity picture that drives work.

Open the DM ledger now (the `## Directives & Memory` section of Comm.md — it ships in the
template) and seed it from the user's request so far. Then **keep capturing, continuously**:

- **Capture trigger (always on, every loop, Tier 0 — no confirmation).** At **every user turn**,
  and whenever **you (Leader) commit a load-bearing design choice**, scan for *durable* items —
  anything that should still constrain work several tasks from now (as opposed to a one-off
  instruction for the current task). When you find one, record it immediately. Capturing and
  recording are writing-records actions, always permitted.
- **Four categories** (tag each entry): `MUST` (a constraint to obey), `REMEMBER` (a fact the
  user told you to keep), `IMPORTANT` (a priority they stressed), `DESIGN` (a design-central
  element/decision). When unsure whether something is durable, capture it — an over-captured
  directive is cheap; a forgotten constraint is a redo.
- **Where it goes (3-tier, like every other record).** The active table lives in Comm.md's
  `## Directives & Memory` with ids `U1, U2, …` (a namespace separate from `T`/`D`/`R`/`OQ`);
  this section is **pinned like `## /goal` and `## Status Summary` — never compressed away**.
  Append each directive's full text to **`comm-reports/directives.md`** (the graphify-feed file —
  initialize it from [assets/directives.template.md](assets/directives.template.md) on first
  capture), add a one-liner to `comm-index.md`'s `## Directives` registry, and when a directive is
  superseded move its rationale to `comm-summary.md`'s `## Leader Profile`. Timestamp every entry
  (date **and** time, from the system clock).
- **Retire superseded directives from the graph feed.** When a directive is superseded, do **not**
  delete its `comm-reports/directives.md` entry (history is preserved) — instead mark it
  `Status: superseded` and move it under that file's `## Superseded` heading, so the next
  `/graphify <path> --update` stops emitting a **live** governance edge for a constraint the user
  has retracted. An append-only feed that never retires entries would re-assert dead constraints
  on every refresh.
- **Feed graphify.** Because `comm-reports/directives.md` sits inside the graphed path, a
  `/graphify <path> --update` turns each directive into a **governance node linked to the
  resources it names** — so the graph now shows not just how code connects, but which directives
  govern which resources. Refresh the graph whenever you add or change a directive. These are
  **authored** nodes (clgem-supplied), kept honestly distinct from EXTRACTED code edges — see
  [references/graphify-integration.md](references/graphify-integration.md).

**Direct work by reading connections *and* records together.** From here on, decide *what to do
next* — which task to spawn, what context a worker needs — by jointly reading (a) the graph's
connectivity signals (god nodes, communities, surprising connections, isolated nodes) and (b) the
records (DM ledger + Leader Decision Log), never from memory alone. The DM ledger tells you the
constraints that must hold; the graph tells you what those constraints touch. Their intersection
is what each task and each worker prompt must carry.

## Step 2 — Plan and populate the Task Board

Decompose the goal into tasks small enough that one worker can finish each in a
single run. For each task record in Comm.md's Task Board: id (`T1`, `T2`, …),
description, assigned role/model, dependencies, status.

Using the Step 1.5 connectivity map (standard unless the path holds a single resource), decompose
along its communities (one worker per cluster where possible), give god-node tasks tighter
constraints and serialized (never parallel) edits, and copy each load-bearing surprising connection
into the Leader Decision Log as a design constraint.

Design the architecture yourself at this step — workers implement your design;
they do not invent their own. Put load-bearing design decisions in the Leader
Decision Log so workers and the Codex reviewer can see the rationale. Read the
**Directives & Memory ledger** as you plan: every `MUST`/`DESIGN` directive is a hard
constraint on the task shapes, and any design-central decision you make here is itself a
`DESIGN` directive — capture it back into the ledger (Step 1.6) so it survives the session.

## Step 3 — Execution loop

Repeat until the goal's acceptance criteria are met:

0. **Loop start check** — before spawning any worker, scan three things and read the
   graph + records together (Step 1.6) to decide what the loop actually needs next:
   - **Active Directives** (DM ledger): re-read every `active` directive. Any `MUST`/`DESIGN`
     directive whose `Governs` set overlaps an upcoming task must be surfaced into that task's
     DESIGN CONSTRAINTS and its worker's `ACTIVE DIRECTIVES` field. If a new user turn added a
     directive, capture it first (Step 1.6) — a directive recorded but not threaded into the
     task that it governs is a directive forgotten.
   - **Open Items**: are any items now actionable? If yes, decide whether to add
     them to this loop's Task Board. Tier 1 items (follow-ups from an ACCEPT'd plan)
     proceed automatically; Tier 2 items (new task types, architectural changes,
     external/irreversible actions) require user confirmation first — ask before acting.
   - **Unfulfilled `next_action` fields** in the Leader Decision Log and in
     `comm-summary.md`: any entry whose `next_action` is not `none` and has no
     corresponding Task Board entry must be added to this loop. This is how committed
     follow-up work is guaranteed to surface. (See Autonomy tiers below.)
1. **Assign** — spawn worker agents with the Agent tool, choosing model per the
   table in references/agents.md. Spawn independent tasks in parallel in one
   message. Use the worker prompt template below — a worker that doesn't know the
   goal or the reporting format produces reports you can't use. Since the Step 1.5
   map is standard, fill each worker's **CONNECTIVITY CONTEXT** from the graph (its target's
   dependents/blast radius, shared data, and nearby god nodes or surprising connections)
   so the worker understands its change's reach while working. Fill its **ACTIVE DIRECTIVES**
   field from the DM ledger — the `U`-ids whose `Governs` set touches this task (read the
   directive→resource edges in the graph to find them), so the worker obeys every standing
   constraint, not just the task instruction.
2. **Collect reports** — each worker's final message is its report. Transcribe the
   essentials into Comm.md (see Comm.md discipline below) and mark the task
   `done-pending-review`.
3. **Independent review** — for every completed task, run an independent critical
   review per [references/codex-review.md](references/codex-review.md).
   Default = **automated background review with Leader waiting**: mark Comm.md Status
   `Claude 대기중 — R<id> 리뷰 완료·기록까지 대기`, spawn **`codex exec` (headless,
   gpt-5.5 high reasoning, verdict written via `-o`)** in the background
   (`run_in_background: true`), and do
   not advance the loop until it finishes and the verdict is read from
   `comm-reports/R<id>-out.txt`. The **opus Fallback Reviewer** (a `general-purpose`
   `opus` worker) is used only when `codex exec` fails twice. When a finding is
   ambiguous or Leader disagrees with it, **resume the review session for follow-up
   dialogue** (`codex exec resume`, Tier 0, 1–2 questions max) before deciding —
   see the reference. After every review, **report the verdict, key findings, and
   the Leader decision to the user in chat** (the user's language); the user never
   needs to read the raw review session. Log the full verdict + findings in Comm.md's Review Log (reviews are
   never condensed). When a connectivity map exists, the review also runs a
   **connectivity-regression check** — god-node edges intact, no new import cycle, no
   newly-isolated component, no broken surprising-connection dependency — against the
   pre-change Connectivity Map snapshot (see
   [references/codex-review.md](references/codex-review.md)). The review also runs a
   **directive-compliance check**: the work must not violate any `active` `MUST`/`DESIGN`
   directive whose `Governs` set it touches — pass the relevant `U`-ids to the reviewer as
   acceptance constraints.
4. **Decide** — for each review, record one of these Leader decisions in Comm.md,
   with a one-line justification:
   - **REDO** — the work misses the goal; reassign with the review findings attached.
   - **SUPPLEMENT** — mostly right; spawn a follow-up task for the gaps.
   - **ACCEPT** — review passed, or findings are out of scope; mark `done`, note
     ignored findings so they aren't silently lost.
4.5. **Verify completeness via graphify (using the standard Step 1.5 map)** — refresh it with
   `/graphify <path> --update`, then treat **isolated nodes** and the report's **Knowledge Gaps**
   as a completeness checklist against the Definition of done; a newly-isolated component or a
   missing expected edge means the work is incomplete. Flag any **new import cycle** or a god node
   that lost edges to the reviewer as a regression signal, and record the delta in Comm.md's
   `## Connectivity Map (Graphify)`. See
   [references/graphify-integration.md](references/graphify-integration.md).
5. **Update the goal** — recompute Completion as
   `(criteria fully met ÷ total criteria) × 100`, counting a criterion as met
   only when its closing evidence (per Definition of done) actually exists. If all
   criteria are met, finish. Otherwise, stop and escalate to the user — with the
   options, instead of looping forever — if either stall guard trips:
   - **Per-task stall**: the same task reaches two REDO cycles.
   - **Global stall**: Completion does not increase across two consecutive loop
     iterations. This catches the case the per-task guard misses — several
     different tasks each churning once while overall progress flatlines.

### Worker prompt template

Every worker prompt must contain, in this order:

```
ROLE: <role name from references/agents.md>
GOAL CONTEXT: <the /goal statement — workers align to the goal, not just the task>
TASK <id>: <precise, bounded instruction — files, expected behavior, constraints>
DESIGN CONSTRAINTS: <Leader's architecture decisions this task must follow>
ACTIVE DIRECTIVES: <from the DM ledger — the U-ids (MUST/DESIGN/REMEMBER/IMPORTANT) whose Governs set touches this task, quoted so the worker obeys every standing user constraint, not just the task instruction. Omit only when no active directive touches this task.>
CONNECTIVITY CONTEXT: <from graphify — what this task's target connects to: dependents/callers (blast radius), shared data, nearby god nodes & surprising connections; mark INFERRED edges as hypotheses. Omit only for a single-resource path where no map was built.>
DO NOT: <scope limits — what the worker must not touch>
REPORT FORMAT: End your final message with exactly:
  STATUS: success | partial | blocked
  CHANGED: <files changed or artifacts produced>
  EVIDENCE: <how you verified it works — command output, test result>
  CONCERNS: <risks, assumptions, anything the reviewer should probe>
```

The REPORT FORMAT matters because the worker's final message is the only thing
returned to you — it must carry everything Comm.md and the Codex reviewer need.

## Comm.md discipline

- **Leader Claude is the sole writer of Comm.md** (and of `comm-index.md` and
  `comm-summary.md`). Parallel workers editing one file corrupt each other's writes;
  workers report via their final message and you transcribe.
- **Actively use all the work-record files — never let everything pile into Comm.md.**
  Each task's durable detail belongs in `comm-reports/T<id>.md` **by default** (not
  only for long-running workers); `comm-index.md` is the living one-line registry of
  tasks/decisions/Q&A; `comm-summary.md` is the rolling rollup (goal, decision
  rationale, full codex reviews, resume checklist). `Comm.md` holds only the **active
  session state** and links out to the others. At every state change, update the
  file that record belongs in — not just Comm.md.
- **Timestamp every entry with date *and* time** (e.g. `2026-06-21 08:40 KST`), not
  just the date — applies to decisions, status updates, review verdicts, and
  worker-report transcriptions across all four files. Obtain the actual current
  local time from the system (e.g. run `date`); never guess or invent it.
- Update Comm.md at every state change — task assigned, report received, review
  logged, decision made — not in one batch at the end.
- **Never delete history; original content is always preserved** in `comm-reports/`,
  `comm-index.md`, or `comm-summary.md` before it leaves Comm.md. The three-tier
  layout keeps Comm.md itself lean (target ≤ 200 lines) while retaining full audit
  trails in the companion files.

### Recording policy — log every agent; condense workers, preserve reviews & Leader reasoning

Comm.md exists so the agents can coordinate and so the work history is remembered —
**who did what, and why.** Every time an agent finishes a unit of work, Leader records
it in Comm.md, attributed to that agent (role + id). How much detail to keep depends
on who produced it:

- **Worker results → condense to the essentials.** Keep only what the next step needs:
  `STATUS`, the load-bearing `CHANGED` artifacts, the key `EVIDENCE`, and any `CONCERNS`
  that affect downstream work. The full worker report is preserved verbatim in
  `comm-reports/T<id>.md`, so Comm.md does not need it in full.
- **Codex (`codex`) critical reviews → record in full, well-organized.** Never
  reduce a review to a bare verdict. Capture the `VERDICT` and the **complete** findings
  list (numbered, most severe first), tidied for readability. The reviewer's independent
  judgment is the safety net of the loop — discarding its detail defeats the gate.
- **Leader Claude's own work → record in full, well-organized.** Decisions, design
  rationale, trade-offs weighed, and why a review finding was accepted or overridden.
  This is the reasoning thread future sessions and other agents rely on; never shrink
  it to a stub.

This asymmetry survives compression: worker detail lives in `comm-reports/`, while
codex reviews and Leader reasoning move **intact** into `comm-summary.md` — never
collapsed to a footnote.

### Lightweight mode (small projects)

When the task board has roughly **5 or fewer tasks** and the project is expected to
finish in a single session, Leader operates in **Lightweight mode**:

- Use **`Comm.md` as the primary coordination surface**, but **still create and
  actively maintain the companion files** (`comm-index.md`, `comm-summary.md`, and
  `comm-reports/T<id>.md`) from the start — Lightweight means *fewer tasks*, not
  *Comm.md only*. Keep the companion files terse for a tiny project, but give each
  record its purpose-built home instead of accumulating everything in Comm.md. This
  keeps Comm.md lean and the audit trail distributed.
- **Promote to full three-tier layout** when either trigger fires:
  (a) `Comm.md` exceeds the ~200-line target, or
  (b) the project spills into a second session. At that point, create `comm-index.md`
  and `comm-summary.md`, run compression trigger 1 and 2, and continue under the
  standard three-tier rules.
- **The ~200-line mark is unambiguous by mode**: in Lightweight mode the *first*
  crossing triggers **promotion** (this is a one-time transition); once promoted (full
  mode), every later crossing triggers **compression** (trigger 3 below). A project is
  therefore only ever in one mode at a time, so the same number never means two things
  at once. (200 is a default heuristic, not measured — adjust if real usage warrants.)
- This gives short projects the simplicity advantage of a single file while long
  projects automatically gain the token-saving, selective-loading benefits of the
  three-tier layout — an adaptive rule rather than a fixed one.

### Three-tier file layout

The three-tier layout trades the simplicity of a single file for token savings and
selective loading — a worthwhile swap for large or long-running projects. For small
projects where simplicity matters more, the Lightweight mode below lets you stay with
a single `Comm.md` until the project grows to warrant the full layout.

If you operate multiple clgem projects concurrently, run each in its own workspace
(or dedicated subdirectory) — sharing a root causes `Comm.md`, `comm-index.md`, and
`comm-summary.md` filename collisions across projects.

| File | Contains | Writer | Growth policy |
| --- | --- | --- | --- |
| `Comm.md` | Active session state only | Leader | ≤ 200 lines; compress on triggers below |
| `comm-index.md` | Full project task registry, one-liner decisions, Q&A | Leader | Append-only; never shrink |
| `comm-summary.md` | Compressed goal, full decision rationale, Session Resume Checklist, Leader Profile | Leader | Replace/append; always current |
| `comm-reports/T<id>.md` | Per-task permanent artifacts | Worker (writes) / Leader (links) | Permanent; never modified after task is done |

### Compression triggers

Apply these in the order listed. After any compression, verify Comm.md line count
is back under 200 before continuing.

1. **Task reaches `done`** → move the full Worker Report for that task to
   `comm-reports/T<id>.md` (create the file if it doesn't exist, appending if it
   does). Remove the `### T<id>` block from `## Worker Reports` in Comm.md. Add a
   one-row summary to `comm-index.md`'s Task Registry. For the corresponding
   Codex review, move its **full** verdict + findings to `comm-summary.md`
   (per the Recording policy — codex reviews are preserved intact, not condensed), and
   leave only a one-line pointer (id + verdict) in `comm-index.md`'s Task Registry row.
2. **Loop iteration ends** → move all Decision Log entries beyond the 5 most recent
   to `comm-summary.md` under `## Architectural Decisions`. Keep only the 5 most
   recent in Comm.md's `## Leader Decision Log`.
3. **Comm.md exceeds ~200 lines** → at the very next state change, perform steps 1
   and 2 as a compression pass before recording the new state change. The `## Status
   Summary`, `## /goal`, and `## Directives & Memory` (active directives only) sections
   are never compressed — they stay in Comm.md. When a directive is superseded, move its
   rationale to `comm-summary.md`'s `## Leader Profile` and drop it from the active table.
4. **`comm-summary.md` `## Codex Reviews` grows excessively large** → for the
   oldest fully-resolved reviews (verdict is final, no open SUPPLEMENT work), condense
   each to a "verdict + 2-3 line key-findings summary" inline in `comm-summary.md` and
   move the full text to `comm-reports/reviews/R<id>.md`, leaving a one-line pointer
   (`→ full text: comm-reports/reviews/R<id>.md`) in its place. The **most recent
   reviews and any review with an in-progress SUPPLEMENT** always retain their full
   text in `comm-summary.md` — never condense active or recent reviews. (This is
   consistent with the Recording policy: active/recent codex reviews remain intact;
   only archived, fully-resolved reviews are condensed, and their full text is preserved
   in `comm-reports/reviews/`.)

## Checkpointing & interruption

Update `## Status Summary` in Comm.md on every state change. The last line of
Status Summary **must always** be `Next action: <one sentence>` — this is the
session resume pointer. A reader (or resumed Leader) must be able to pick up work
from Status Summary alone without reading the rest of Comm.md.

**When a session ends with active tasks still in flight** (user closes the conversation,
or Leader detects the session is about to terminate), Leader must write or update the
`## Interrupted State` section in Comm.md as the very last action:

```markdown
## Interrupted State

- **Interrupted at**: <YYYY-MM-DD HH:MM TZ>
- **In-progress tasks**: <T-ids and their last known state>
- **Last worker output summary**: <one sentence per task>
- **Next action on resume**: <precise first action — e.g., "Run codex review on T3 report, then decide ACCEPT/REDO">
```

On the next session resume, read `## Interrupted State` (if present), act on
"Next action on resume", then remove the section from Comm.md.

## Autonomy tiers

These tiers guide Leader's judgment about when to act immediately versus when to
pause and confirm. They are **behavioral guidelines, not enforcement mechanisms** —
the goal is predictable, trustworthy initiative, not autonomous overreach.

| Tier | Category | Examples | Action |
| --- | --- | --- | --- |
| **0** | Always permitted — no confirmation needed | Running codex reviews (launching the separate codex console/process is always allowed — the review gate is the loop's safety net, never gated by Tier 2); writing Comm.md / comm-index.md / comm-summary.md; updating status and checkpoints; read-only reconnaissance (Scout tasks) | Proceed immediately |
| **1** | Permitted — log in Decision Log | Spawning a follow-up task that extends an already-ACCEPT'd plan; executing a recorded `next_action` from the Decision Log; re-assigning an `in-progress` task on resume (prior worker report exists) | Proceed; record in Leader Decision Log with `next_action: none` |
| **2** | Requires user confirmation before acting | Architectural changes; introducing a new task type not in the current plan; any external/irreversible action (MCP calls, network requests, deployment, bulk file deletion, new external integrations). **Exception: launching the codex review session (a separate console/process) is always Tier 0 — see above.** | Stop; present options to user; wait for explicit approval |

Record every Tier 1 decision in the Leader Decision Log with its justification.
For Tier 2 situations, present the options and rationale to the user — do not
unilaterally proceed even if the action seems obviously correct.

### Leader Decision Log format

Each entry in `## Leader Decision Log` (in Comm.md) must follow this structure:

```
- <YYYY-MM-DD HH:MM TZ> — <decision title and one-line rationale>
  - **next_action**: <task to spawn in the next loop iteration, or "none">
```

Use the actual current local date **and time** (obtain it from the system, e.g.
`date`), not just the date — this applies to every timestamped entry in Comm.md,
comm-index.md, and comm-summary.md.

At the start of each loop iteration (Step 3, loop-start check), scan all Decision
Log entries (in Comm.md and in `comm-summary.md`'s Architectural Decisions) for
unfulfilled `next_action` values. Any entry with a `next_action` that is not `none`
and has no corresponding Task Board entry must be added to the current loop's Task
Board — this is the committed follow-up guarantee.

## Finishing

When all acceptance criteria are met: set Completion to 100%, write a final
status section in Comm.md (what was delivered, evidence per criterion, ignored
review findings), and summarize for the user — outcome first, then how each
criterion was verified. Also update `comm-summary.md`'s `## Completed Work` and
`## Known Risks & Deferred Items` so the project record is fully consolidated.

With the standard Step 1.5 map, the completeness check (no unexplained isolated nodes, no new
import cycles, god-node edges intact) is part of the closing evidence per criterion.
