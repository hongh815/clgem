# clgem Antigravity Review Gate

In clgem the Antigravity review is **not optional** — every completed task passes
through it before Leader Claude marks it done. An independent model catches what a
same-model reviewer rationalizes away; that independence is the point of paying for
the extra session. The reviewer is the **Antigravity CLI** (command `agy`) running
the **Gemini 3.1 Pro (High)** model — the High reasoning tier is chosen because
review quality is the safety net of the whole loop.

## Headless capture — agy IS capturable via scripts/agy_review.py (verified v1.0.10)

The **naive path still fails**: `agy -p` / `--print` with stdout as a pipe, file, or
redirect returns exit 0 with **empty output** — agy renders only to a real TTY. So
bare `agy -p` is NOT usable for background capture.

The **working method**: `scripts/agy_review.py` spawns agy inside a real ConPTY via
**pywinpty** with an **explicit non-zero size** (`dimensions=(50, 200)`). That
non-zero size defeats the old winpty `cols=0` assertion that used to kill real
reviews under agy v1.0.9. stdout is captured, ANSI-stripped, and written to an
output file — headless, background, auto-recorded.

**VERIFIED on agy v1.0.10 (Windows):** captured BOTH a trivial prompt AND a full
critical review launched with `--add-dir` (real multi-finding reasoning that read
workspace files). The v1.0.9-era "six capture methods all failed / cannot be
captured headlessly" conclusion is therefore **RETIRED**.

**Requirement:** Python + `pywinpty` (`pip install pywinpty`). If pywinpty or Python
is unavailable, fall back to the opus Fallback Reviewer (see Failure handling).

### Optional: agy live window (a human watches)

An interactive `agy --prompt-interactive` window launched via
`cmd //c start ... powershell -NoExit` remains available when a human wants to watch
the review stream and handle auth/permission prompts directly. Running it in parallel
with the captured review is an optional **dual independent review** — two different-
vendor verdicts on the same task — but this is **optional**, not the default. The
default captured review via `scripts/agy_review.py` is sufficient and fully
auto-recorded.

## Automated background review — Leader waits (default)

The default reviewer is **agy captured via `scripts/agy_review.py`** (headless,
background, auto-recorded). Procedure:

1. **Mark waiting.** In Comm.md set `## Status Summary` to e.g.
   `Claude 대기중 — R<id> 리뷰 완료·기록까지 대기` and the agy reviewer's Agent
   Roster row to `Active`.
2. **Write the review prompt** → `comm-reports/R<id>-prompt.txt` (use the template
   below).
3. **Spawn the capture** via Bash with `run_in_background: true`:

   ```bash
   python "$HOME/.claude/skills/clgem/scripts/agy_review.py" \
     "comm-reports/R<id>-prompt.txt" "comm-reports/R<id>-out.txt" \
     "Gemini 3.1 Pro (High)" "5m" --add-dir "<artifact dir to review>"
   ```

   Reference `agy_review.py` by the skill's own path so it works regardless of cwd
   **and across users** — `$HOME/.claude/skills/clgem/scripts/agy_review.py` (Bash)
   or `%USERPROFILE%\.claude\skills\clgem\scripts\agy_review.py` (Windows cmd); do
   not hardcode a specific user's home. The first two positional args are
   `<prompt_file> <out_file>`, then `<model> <print_timeout>`, then any number of
   `--add-dir <dir>` (repeatable — e.g. add `<workspace>/graphify-out` for the
   connectivity check). For large artifacts, pass `--add-dir <dir>` and reference
   file paths in the prompt instead of pasting.

4. **Wait.** Do not advance the loop while the review runs; Leader stays in the
   waiting state. When the background capture finishes, READ
   `comm-reports/R<id>-out.txt` — that file is the captured verdict.
5. **Record + proceed.** Transcribe the **full** verdict + findings into Comm.md's
   Review Log (per the Recording policy — reviews are never condensed), make the
   Leader decision, then clear the waiting state and continue.

Note: the opus Fallback Reviewer (below) is used only when agy capture fails (see
Failure handling).

## Invocation — visible interactive window (optional human-watch mode)

When a human wants to watch the review stream live and handle auth/permission prompts
directly, launch an interactive agy window. This is **optional** alongside the
captured review — not the default path.

Two facts about the installed build (confirmed agy v1.0.10):

- `agy -p` / `--print` with stdout as a pipe/file/redirect returns **exit 0 with
  empty output** — agy renders only to a real TTY. Headless capture goes through
  `scripts/agy_review.py` (NOT bare `agy -p`).
- A new window launched with PowerShell `Start-Process` may not surface on the
  user's desktop. `cmd start` does reliably pop a window.

1. **Write the prompt** → `comm-reports/R<id>-prompt.txt` (the template below).

2. **Write the runner** → `comm-reports/R<id>-run.ps1`:

   ```powershell
   $ErrorActionPreference = 'Continue'
   $p = Get-Content "$PSScriptRoot\R<id>-prompt.txt" -Raw
   # 대화형(-i / --prompt-interactive): 초기 프롬프트 실행 후 세션 유지.
   agy --prompt-interactive $p `
       --model "Gemini 3.1 Pro (High)" `
       --add-dir "<skill or artifact dir>"
   ```

3. **Open it in a visible window** (Bash tool; use `cmd start`, not `Start-Process`):

   ```bash
   RUN='<workspace>\comm-reports\R<id>-run.ps1'   # the project's own comm-reports path
   cmd //c start "clgem R<id> review" powershell -NoExit -ExecutionPolicy Bypass -File "$RUN"
   ```

4. **Collect the verdict**: after the user confirms agy has finished, ask them to paste
   the final `VERDICT: …` / `FINDINGS: …` block (or read it from the window). Leader
   transcribes it into Comm.md. The window stays open (`-NoExit`) so the full review
   is scrollable.

### Notes on the installed `agy` build (confirmed against v1.0.10)

- `agy --version` is the Step 0 availability probe (confirmed v1.0.10).
- `--model` takes the exact model string as printed by `agy models` (quote it — it
  contains spaces and parentheses). Use `"Gemini 3.1 Pro (High)"` for review.
  Confirmed models (v1.0.10): `Gemini 3.5 Flash (Low/Medium/High)`,
  `Gemini 3.1 Pro (Low/High)`, `Claude Sonnet 4.6 (Thinking)`,
  `Claude Opus 4.6 (Thinking)`, `GPT-OSS 120B (Medium)`. `-i` = `--prompt-interactive`,
  `-p` = `--print` (no `-m` short form for model).
- For large artifacts, don't paste them — add the directory with `--add-dir`
  (repeatable) and reference the file paths in the prompt.
- Headless capture goes through `scripts/agy_review.py` (pywinpty, ConPTY,
  `dimensions=(50, 200)`) — NOT bare `agy -p`.

## Review prompt template

Give the reviewer everything it needs to be genuinely critical — the goal, the
claim, and the evidence — and explicitly license it to fail the work:

```
You are an independent critical reviewer. Your job is to find what is wrong,
missing, or divergent from the goal — not to be agreeable. If you cannot verify
a claim, say so.

PROJECT GOAL: <the /goal statement and acceptance criteria>
TASK <id>: <what the worker was asked to do>
WORKER REPORT: <the worker's STATUS/CHANGED/EVIDENCE/CONCERNS block>
ARTIFACTS: <relevant file contents or diff — paste the actual content, OR, if
you launched agy with --add-dir, reference the exact file paths to review>
ACTIVE DIRECTIVES (acceptance constraints): <the U-ids + quoted MUST/DESIGN directive text
from Comm.md's `## Directives & Memory` whose `Governs` set this task touches. The work must
NOT violate any of these — treat a violation as a failing finding.>
CONNECTIVITY (when a graphify map exists): the post-change graph in `graphify-out/`
(`GRAPH_REPORT.md` for god nodes / import cycles / knowledge gaps, `graph.json` for raw edges) and
the pre-change `## Connectivity Map (Graphify)` snapshot from Comm.md. For agy add
`--add-dir <workspace>/graphify-out`; the opus reviewer reads those files directly.

Review for: correctness, missing edge cases, divergence from the goal,
unverified claims in the report, risks the worker did not mention, **directive regression**: the
change must not violate any listed `ACTIVE DIRECTIVES` `MUST`/`DESIGN` constraint (cite the U-id
and the violating change), and — when a graphify
connectivity map exists — **connectivity regression**: a god node that dropped edges it should
keep, a new import cycle, a newly-created component left isolated (≤1 connection), or a broken
surprising-connection dependency the plan relied on (cite the specific node/edge).

End with exactly:
VERDICT: PASS | CONDITIONAL | FAIL
FINDINGS: <numbered list, most severe first>
```

Paste real artifact content into the prompt — a review of a summary is a summary
of a review.

## Connectivity-regression check (when a graphify map exists)

clgem builds a graphify connectivity map as a standard step (see
[graphify-integration.md](graphify-integration.md)), so every review includes an explicit
connectivity-regression pass. The reviewer reads the **post-change** graph in `graphify-out/`
(`GRAPH_REPORT.md` for god nodes, import cycles, and knowledge gaps; `graph.json` for the raw
edges) and compares it against the **pre-change** `## Connectivity Map (Graphify)` snapshot the
Leader recorded in Comm.md. It fails or conditions the task when the change:

- drops edges from a **god node** it should have preserved,
- introduces a **new import cycle**,
- leaves a **newly-created component isolated** (≤1 connection), or
- breaks a **surprising-connection dependency** the plan relied on.

Each is reported as a numbered FINDING citing the specific node/edge. Connectivity findings are
evidence the gate weighs — they sharpen, but do not replace, the reviewer's correctness judgment.

## Logging and the Leader decision

Log every review in Comm.md's Review Log: review id (`R1`, `R2`, …), target task id,
verdict, and the **complete** findings list — per the Recording policy, reviews are
**never condensed** (the scanning table may hold just id/verdict/decision, but the
full verdict + findings go in the per-review block). Then record the Leader decision
— **REDO / SUPPLEMENT / ACCEPT** — with its rationale. The justification is mandatory
for ACCEPT-despite-findings: an ignored finding without a recorded reason is
indistinguishable from an overlooked one.

Findings feed forward: when a task is reassigned (REDO) or extended
(SUPPLEMENT), attach the relevant findings verbatim to the new worker prompt.

## Failure handling

- agy capture (via `scripts/agy_review.py`) errors, times out, or returns EMPTY
  output → retry once.
- Second failure (or pywinpty/Python unavailable) → log it in Comm.md and use the
  **opus Fallback Reviewer** (a `general-purpose` `opus` worker,
  `run_in_background: true`, given the same review prompt template). Note in the
  Review Log that the review was same-vendor (Claude), so its independence is weaker.
- An unusable response (no VERDICT, off-topic) → treat as a failure, not PASS.

## Escalation

Two consecutive FAIL verdicts on the same task mean the problem is the plan, not
the worker. Leader Claude stops the loop, re-examines the architecture for that
task, and either re-designs it or escalates to the user with the trade-offs.
