---
name: clgem
description: >-
  Claude-led multi-agent project orchestration ("clgem"). Leader Claude (Fable 5)
  designs the architecture, plans, allocates tasks to cost-optimized worker agents,
  and verifies results; a separate Gemini CLI session critically reviews every
  completed task; all coordination is logged in Comm.md; work iterates against a
  /goal until acceptance criteria are met. Use this skill whenever the user invokes
  /clgem, mentions clgem or Leader Claude, asks to run an entire project
  systematically with an orchestrated agent team, wants Comm.md-based agent
  coordination, asks for Gemini-verified execution, or wants goal-driven
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
4. **Verification** — judge every result against the goal, informed by Gemini's
   independent critical review.

Worker agents execute faithfully and report back; a **separate Gemini CLI session**
reviews every completed task critically; **Comm.md** is the single shared ledger
that lets you track progress in real time and plan the next step. Work continues
until the **/goal** acceptance criteria are met — not until the first draft exists.

## Step 0 — Session setup (once per project)

1. If `Comm.md` does not exist in the workspace root, create it from
   [assets/Comm.template.md](assets/Comm.template.md). If it exists, read it first —
   it may contain state from a previous clgem session you must continue, not overwrite.
2. Check the review channel: run `gemini --version` (Bash). If the Gemini CLI is
   unavailable, record that in Comm.md and use the fallback reviewer defined in
   [references/gemini-review.md](references/gemini-review.md).
3. Read [references/agents.md](references/agents.md) for the role and model table
   before spawning any worker.
4. Confirm the Leader model: Leader Claude runs on **Fable 5**. If Fable 5 is not
   available in this session, fall back to **Opus 4.8** (`claude-opus-4-8`) — never
   to a worker-tier model. Record the active Leader model in Comm.md.

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

The goal is the contract for the whole session. Every Gemini review and every
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
Decision Log so workers and Gemini can see the rationale.

## Step 3 — Execution loop

Repeat until the goal's acceptance criteria are met:

1. **Assign** — spawn worker agents with the Agent tool, choosing model per the
   table in references/agents.md. Spawn independent tasks in parallel in one
   message. Use the worker prompt template below — a worker that doesn't know the
   goal or the reporting format produces reports you can't use. Since the Step 1.5
   map is standard, fill each worker's **CONNECTIVITY CONTEXT** from the graph (its target's
   dependents/blast radius, shared data, and nearby god nodes or surprising connections)
   so the worker understands its change's reach while working.
2. **Collect reports** — each worker's final message is its report. Transcribe the
   essentials into Comm.md (see Comm.md discipline below) and mark the task
   `done-pending-review`.
3. **Gemini review** — for every completed task, run a Gemini CLI review as a
   separate session per [references/gemini-review.md](references/gemini-review.md).
   Log the verdict in Comm.md's Review Log. Reviews of finished tasks can run in
   the background while the next task executes. When a connectivity map exists, the
   review also runs a **connectivity-regression check** — god-node edges intact, no
   new import cycle, no newly-isolated component, no broken surprising-connection
   dependency — against the pre-change Connectivity Map snapshot (see
   [references/gemini-review.md](references/gemini-review.md)).
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
CONNECTIVITY CONTEXT: <from graphify — what this task's target connects to: dependents/callers (blast radius), shared data, nearby god nodes & surprising connections; mark INFERRED edges as hypotheses. Omit only for a single-resource path where no map was built.>
DO NOT: <scope limits — what the worker must not touch>
REPORT FORMAT: End your final message with exactly:
  STATUS: success | partial | blocked
  CHANGED: <files changed or artifacts produced>
  EVIDENCE: <how you verified it works — command output, test result>
  CONCERNS: <risks, assumptions, anything the reviewer should probe>
```

The REPORT FORMAT matters because the worker's final message is the only thing
returned to you — it must carry everything Comm.md and Gemini need.

## Comm.md discipline

- **Leader Claude is the sole writer of Comm.md.** Parallel workers editing one
  file corrupt each other's writes; workers report via their final message and you
  transcribe. If a long-running worker needs to leave a durable artifact, have it
  write `comm-reports/T<id>.md` and link it from Comm.md.
- Update Comm.md at every state change — task assigned, report received, review
  logged, decision made — not in one batch at the end. The file is how the user
  (and a resumed session) sees real-time progress.
- Never delete history; append. Move stale items to a `## Archive` section if the
  file grows unwieldy.

## Finishing

When all acceptance criteria are met: set Completion to 100%, write a final
status section in Comm.md (what was delivered, evidence per criterion, ignored
review findings), and summarize for the user — outcome first, then how each
criterion was verified.

With the standard Step 1.5 map, the completeness check (no unexplained isolated nodes, no new
import cycles, god-node edges intact) is part of the closing evidence per criterion.
