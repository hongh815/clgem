# Graphify-Aware Skill Authoring and Cross-Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach clgem to use Graphify when authoring skills and to invoke Antigravity as an optional independent second reviewer.

**Architecture:** Keep Codex as the default review gate. Add a concise skill-authoring reference for Graphify procedures and a separate Antigravity review reference for independent, sandboxed, non-interactive reviews. Wire both into existing orchestration and roster guidance.

**Tech Stack:** Markdown plugin skill documents; Graphify CLI; Antigravity CLI (`agy`).

## Global Constraints

- Codex remains the mandatory default reviewer.
- Antigravity must not see Codex's verdict before its own verdict is written.
- Treat Graphify INFERRED and AMBIGUOUS edges as hypotheses.
- Do not alter pre-existing untracked files.

---

### Task 1: Document Graphify-aware skill authoring

**Files:**
- Create: `plugins/clgem/skills/clgem/references/skill-authoring.md`
- Modify: `plugins/clgem/skills/clgem/SKILL.md`
- Test: Markdown link and command-reference checks

**Interfaces:**
- Consumes: `graphify-out/graph.json` when present and Graphify CLI commands.
- Produces: a reusable procedure for workers creating or modifying skills.

- [ ] **Step 1: Add the skill-authoring reference**

Define the trigger (creating or modifying a skill), whole-path mapping rule, pre-edit
query/explain/path usage, post-edit `graphify update .`, and evidence/hypothesis
distinction.

- [ ] **Step 2: Link it from orchestration guidance**

Add an explicit instruction in `SKILL.md` that tasks creating or changing skills must
read and apply `references/skill-authoring.md`.

- [ ] **Step 3: Verify documentation references**

Run: `rg -n "skill-authoring|graphify update" plugins/clgem/skills/clgem`

Expected: the new reference and its caller are present.

### Task 2: Add Antigravity secondary critical-review guidance

**Files:**
- Create: `plugins/clgem/skills/clgem/references/antigravity-review.md`
- Modify: `plugins/clgem/skills/clgem/SKILL.md`
- Modify: `plugins/clgem/skills/clgem/references/agents.md`
- Modify: `plugins/clgem/skills/clgem/references/codex-review.md`
- Test: CLI capability and cross-reference checks

**Interfaces:**
- Consumes: `agy -p --sandbox`, task artifacts, directives, and Graphify reports.
- Produces: a secondary `VERDICT: PASS | CONDITIONAL | FAIL` and evidence-backed findings.

- [ ] **Step 1: Add Antigravity reviewer procedure**

Document when to invoke it, a prompt that excludes Codex's verdict, the sandboxed
non-interactive command, persisted output, failure handling, and disagreement process.

- [ ] **Step 2: Wire selection and recordkeeping into clgem**

Add the optional reviewer to the roster and execution loop. Require both review records
and evidence-based resolution when the secondary review runs.

- [ ] **Step 3: Verify command capability**

Run: `agy --version; agy --help`

Expected: a version plus `--print`/`-p` and `--sandbox` options.

- [ ] **Step 4: Run a harmless non-interactive probe**

Run: `agy --sandbox -p "Reply with exactly: AGY_REVIEW_READY"`

Expected: `AGY_REVIEW_READY` without a permission prompt.

### Task 3: Validate the plugin documentation package

**Files:**
- Modify: `plugins/clgem/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Test: JSON parsing and targeted documentation scans

**Interfaces:**
- Consumes: updated skill and review references.
- Produces: versioned marketplace metadata that accurately states the cross-review capability.

- [ ] **Step 1: Update version and descriptions**

Bump the plugin patch version and mention optional Antigravity cross-review alongside
the default Codex review.

- [ ] **Step 2: Validate JSON and references**

Run: `Get-Content -Raw plugins/clgem/.claude-plugin/plugin.json | ConvertFrom-Json; Get-Content -Raw .claude-plugin/marketplace.json | ConvertFrom-Json; rg -n "antigravity-review|skill-authoring|Codex Reviewer|Antigravity" plugins/clgem .claude-plugin`

Expected: both JSON files parse and every reference resolves to the intended new procedure.
