# clgem ↔ graphify Integration — Connectivity-aware planning & completeness

clgem uses the **/graphify** knowledge graph to **connect and understand every resource in the
designated path** — code, docs, papers, images, video — so the Leader and workers plan and act with
a precise, intent-aligned picture of how everything actually interconnects. It is used at three
points: **planning**, **worker context (while working)**, and **completeness verification**. Building
the connectivity map is a **standard step, not an optional optimization**: per the user's intent,
comprehensive understanding takes priority over saving tokens.

## Build the connectivity map (standard step — cover the whole path)

By default, **build or refresh the graph over the entire designated path** before planning — do not
trim it to save tokens. Cover **all resource types** graphify supports (code, docs, papers, images,
video), because cross-resource links — a doc that explains a module, a diagram that maps components —
are exactly the connections that make planning precise and intent-aligned.

- Prefer **thorough extraction**: pass **`--mode deep`** for richer INFERRED connectivity on any
  non-trivial path.
- If graphify warns the corpus is large and offers to **narrow** to a subfolder, **do not narrow** by
  default — the user prioritizes connecting *all* resources over token cost. Narrow only if the path
  is so large the build is genuinely impractical, and record that limitation in Comm.md.
- Reuse a fresh existing `graphify-out/graph.json` (refresh with `/graphify <path> --update`) instead
  of rebuilding from scratch.
- Skip only when the designated path holds essentially a single resource with nothing to
  interconnect — and even then, prefer a quick build if a graph would add any clarity.

Commands: first build `/graphify <path>` (add `--mode deep` for depth); refresh after changes
`/graphify <path> --update`. Building/refreshing the graph is **Autonomy Tier 0** (read-mostly
reconnaissance + a local cache under `graphify-out/`) — no user confirmation needed. The Leader may
invoke /graphify directly, or assign a general-purpose worker to run it; the read-only Scout
(Explore) can interpret an existing graph but cannot write graph files.

## If graphify is not installed (clgem does not bundle it)

graphify is a **separate, third-party** Claude Code skill (by safishamsi —
https://github.com/sponsors/safishamsi) plus the `graphifyy` PyPI package. clgem **uses** it but
does **not** bundle or redistribute it. Before the first connectivity build, confirm graphify is
available — run `graphify --version` (Bash) and check that the `/graphify` skill is present.

If it is **missing**, the Leader **guides the user to install it** instead of failing:
- Python package: `pip install graphifyy` (or `uv tool install graphifyy`).
- graphify Claude Code skill: install it into `~/.claude/skills/graphify/` from the graphify
  project's own source (third-party — obtain it from there; clgem does not ship it).

The `graphifyy` package alone is **not** enough — clgem invokes the `/graphify` **skill**, which in
turn drives the package, so **both** must be present.

If the user installs it, proceed with the standard build. If graphify **stays unavailable** (the
user declines, or is offline), clgem **proceeds without the connectivity map** — Step 1.5, the
worker CONNECTIVITY CONTEXT, and the reviewer connectivity-regression check are skipped — and the
Leader **records that gap in Comm.md's `## Connectivity Map (Graphify)`** (e.g. "graph skipped:
graphify not installed — install guided") so it is a deliberate, visible non-step. Never block the
whole project on this optional external dependency. (You skip here because the tool is **absent**,
not to save tokens — the comprehensive-build rule above still stands when graphify is available.)

## Planning-stage usage

Before decomposing the goal into tasks (Step 1.5 → Step 2), read three graph signals and let
them shape the plan:

1. **God nodes** (most-connected nodes) = the core abstractions with the largest blast radius.
   Tasks that touch a god node get **tighter design constraints and mandatory careful review**;
   never parallelize two workers editing the same god node — serialize them.
2. **Communities** (detected clusters) = natural module boundaries. Use them as **task-decomposition
   seams**: prefer one worker per community; explicitly flag any task that must cross a community
   boundary, because cross-cutting work is where regressions hide.
3. **Surprising connections** (INFERRED cross-community edges) = hidden / non-obvious dependencies.
   Record each relevant one as an explicit **DESIGN CONSTRAINT in the Leader Decision Log** so
   workers do not unknowingly break it.

Honesty rule: graphify marks edges EXTRACTED / INFERRED / AMBIGUOUS. Treat INFERRED and
AMBIGUOUS edges as **hypotheses to verify**, not facts — confirm before relying on them.

## Worker-context usage — understanding while working

When assigning a task, give the worker the **connectivity context** for what it will touch, pulled
from the graph: which nodes **depend on** the target (callers/dependents = blast radius), what data or
edges it **shares**, and any **god node** or **surprising connection** it sits near. A worker that sees
the full set of resources its change connects to edits **precisely and completely** — it won't miss a
caller or break a hidden dependency. Populate the worker prompt's **CONNECTIVITY CONTEXT** field from
`graphify explain <node>` and `graphify query "what connects to X"`, and mark INFERRED / AMBIGUOUS
edges as hypotheses, not facts.

## Completeness-check usage

During Step 3's "Update the goal" step and again at Finishing:

1. Refresh the graph: `/graphify <path> --update`.
2. Use **isolated nodes** (≤1 connection) and the report's **Knowledge Gaps** as a
   **completeness checklist**. A newly-created component that comes back isolated usually means a
   missing wire-up; an expected edge that is absent means the work is incomplete. Cross-check each
   against the goal's Definition of done.
3. Compare **import cycles** and **god-node edge counts** before vs after the change. A new import
   cycle, or a god node that silently lost edges, is a **regression signal** — hand it to the
   reviewer as evidence.
4. Record the graph delta (new/lost god nodes, new cycles, remaining gaps) in Comm.md's
   `## Connectivity Map (Graphify)` section.

## How it pairs with the review gate

The independent reviewer (the Gemini CLI reviewer, or the opus Fallback Reviewer) runs an explicit
**connectivity-regression check**: it reads the post-change graph in `graphify-out/`
(`GRAPH_REPORT.md` + `graph.json`) and compares it against the pre-change `## Connectivity Map
(Graphify)` snapshot in Comm.md, failing or conditioning the task on a dropped god-node edge, a new
import cycle, a newly-isolated component, or a broken surprising-connection dependency. These
connectivity findings are **evidence that feeds the review gate** — they sharpen, but do not
replace, the reviewer's correctness judgment. See
[gemini-review.md](gemini-review.md) for the review procedure.

## Cost & honesty

- The connectivity map is built **comprehensively by design**: per the user's intent, precise
  intent-aligned understanding of all resources outranks token economy, so do not skip or trim the
  graph to save tokens. Record in Comm.md what path was graphed and at what depth.
- Never present INFERRED/AMBIGUOUS edges to workers or the user as confirmed facts.
- If the graph was skipped, record that decision (and why) in Comm.md, so a resumed session knows
  connectivity was a deliberate non-step, not an omission.
