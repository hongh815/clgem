# clgem Codex Review Gate

In clgem the Codex review is **not optional** — every completed task passes
through it before Leader Claude marks it done. An independent model catches what a
same-model reviewer rationalizes away; that independence is the point of paying for
the extra session. The reviewer is the **Codex CLI** (command `codex`) running
**gpt-5.5 with high reasoning effort** — the high tier is chosen because review
quality is the safety net of the whole loop.

## Headless execution — `codex exec` is natively non-interactive

`codex exec` runs headlessly out of the box: it accepts the prompt on stdin, streams
progress to stdout, and writes the agent's **final message to a file** via
`-o/--output-last-message`. No PTY capture script or TTY workaround is needed.

**Requirement:** Codex CLI installed and logged in (`codex --version` is the Step 0
availability probe; verified against codex-cli 0.139.0). If the CLI is unavailable,
fall back to the opus Fallback Reviewer (see Failure handling).

## Automated background review — Leader waits (default)

The default reviewer is **`codex exec`** (headless, background, auto-recorded).
Procedure:

1. **Mark waiting.** In Comm.md set `## Status Summary` to e.g.
   `Claude 대기중 — R<id> 리뷰 완료·기록까지 대기` and the Codex reviewer's Agent
   Roster row to `Active`.
2. **Write the review prompt** → `comm-reports/R<id>-prompt.txt` (use the template
   below).
3. **Spawn the review** via Bash with `run_in_background: true`:

   ```bash
   codex exec \
     -m gpt-5.5 -c model_reasoning_effort=high \
     -s read-only --skip-git-repo-check --color never \
     --cd "<workspace>" \
     -o "comm-reports/R<id>-out.txt" \
     - < "comm-reports/R<id>-prompt.txt" \
     > "comm-reports/R<id>-live.log" 2>&1
   ```

   The `> R<id>-live.log` redirect captures codex's streamed progress (session
   id, commands run, token usage). It is the diagnostic record when a review
   fails (see Failure handling), and it holds the **session id** Leader needs
   for follow-up dialogue with the reviewer (below).

   Flag notes:
   - `-m gpt-5.5 -c model_reasoning_effort=high` — pin the review model and force
     the high reasoning tier regardless of the user's `~/.codex/config.toml` default.
   - `-s read-only` — the reviewer only reads; it must never modify the workspace.
     Set `--cd "<workspace>"` to the project root and keep everything the review
     needs **under it**, referencing exact file paths in the prompt instead of
     pasting large artifacts. Read access outside `--cd` is NOT guaranteed by the
     sandbox — if an artifact lives outside the workspace, copy it into
     `comm-reports/` first.
   - `--skip-git-repo-check` — reviews must work in non-git workspaces too.
   - **no `--ephemeral`** — the review session is deliberately persisted so
     Leader can resume it for follow-up questions (see Follow-up dialogue below).
   - `--color never` + `-o` — `-o` writes the **final message only** (the verdict
     block) to `comm-reports/R<id>-out.txt`, plain text, ready to transcribe.
   - `- < prompt.txt` — read the prompt from stdin; avoids shell-quoting issues
     with long multi-line prompts.

4. **Wait.** Do not advance the loop while the review runs; Leader stays in the
   waiting state. When the background task finishes, READ
   `comm-reports/R<id>-out.txt` — that file is the verdict. If the process runs
   past ~10 minutes with no output file, treat it as a timeout (see Failure
   handling).
5. **Record + proceed.** Transcribe the **full** verdict + findings into Comm.md's
   Review Log (per the Recording policy — reviews are never condensed), make the
   Leader decision, then clear the waiting state and continue.

Note: the opus Fallback Reviewer (below) is used only when `codex exec` fails (see
Failure handling).

## Follow-up dialogue — Leader interrogates the reviewer (Tier 0)

The review is not a one-shot verdict drop: because the review session is
persisted (no `--ephemeral`), Leader can **resume it and ask targeted follow-up
questions** before making the REDO/SUPPLEMENT/ACCEPT decision. Use this whenever
a finding is ambiguous, seems wrong, or needs a concrete reproduction — deciding
on a finding Leader doesn't fully understand wastes a REDO cycle.

1. **Get the session id** from the header of `comm-reports/R<id>-live.log`
   (`session id: <uuid>`).
2. **Ask the follow-up** (Bash, `run_in_background: true`, same waiting rule):

   ```bash
   codex exec resume "<session-id>" \
     --skip-git-repo-check \
     -c sandbox_mode='"read-only"' \
     -o "comm-reports/R<id>-followup<n>-out.txt" \
     "<targeted question — e.g. 'Finding 2: cite the exact line that violates U3
     and show the failing input.'>" \
     >> "comm-reports/R<id>-live.log" 2>&1
   ```

   The reviewer answers with its full review context intact — no need to re-send
   the goal, report, or artifacts.

   Verified flag caveats (codex-cli 0.139.0): `resume` does NOT accept `-s`,
   `--cd`, or `--color`, and it does NOT inherit the original session's
   `read-only` sandbox — a bare resume runs `workspace-write`. The
   `-c sandbox_mode='"read-only"'` override is therefore **mandatory** to keep
   the reviewer read-only (the quoting passes the TOML string `"read-only"`).
3. **Record the Q&A** in the same `R<id>` block of Comm.md's Review Log (question
   + answer, kept in full like the review itself). The follow-up answer is part
   of the review record and feeds the Leader decision.

Ground rules:

- Follow-ups are for **clarifying the existing review** (probe a finding, request
  evidence, test a counter-argument). They are NOT for re-reviewing changed work —
  after a REDO/SUPPLEMENT, run a **fresh review** (`R<id+1>`) on the new artifacts.
- Keep it bounded: 1–2 follow-ups per review. If the verdict is still ambiguous
  after that, treat it as CONDITIONAL and decide with what you have.
- Follow-up dialogue is **Tier 0** (same as launching the review itself).
- Challenge honestly: if Leader disagrees with a finding, put the counter-argument
  to the reviewer and let it respond before overriding — an override recorded
  after the reviewer conceded (or held firm) is far more trustworthy than a
  unilateral one. Record who yielded and why in the Review Log.

## Reporting to the user — Leader is the communication channel

The user does not watch the reviewer; **Leader relays**. After every review
(and any follow-up dialogue), report to the user in chat, in the user's
language:

- the verdict (PASS / CONDITIONAL / FAIL),
- the findings that matter (severe first, condensed honestly — never hide a
  finding Leader chose to override),
- the Leader decision (REDO / SUPPLEMENT / ACCEPT) and its one-line rationale,
- any follow-up Q&A that changed the decision.

This chat report is a summary for the user; the full record still goes to
Comm.md's Review Log per the Recording policy (reviews are never condensed
there).

### Notes on the installed `codex` build (confirmed against codex-cli 0.139.0)

- `codex --version` is the Step 0 availability probe.
- `-m/--model` takes the model id (`gpt-5.5`); reasoning effort is set separately
  via `-c model_reasoning_effort=high` (config-override syntax, not a dedicated flag).
- `codex exec` has no built-in wall timeout — enforce one from the caller side
  (treat >~10 min with no `R<id>-out.txt` as a failed attempt).
- In the `read-only` sandbox the reviewer cannot write or run mutating commands —
  exactly the posture a reviewer should have. Do NOT use `workspace-write` or
  `danger-full-access` for reviews. Do not rely on reads outside `--cd`: keep all
  review artifacts under the workspace.
- For large artifacts, don't paste them into the prompt — pass `--cd <workspace>`
  and reference the exact file paths in the prompt.

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
ARTIFACTS: <relevant file contents or diff — paste the actual content, OR
reference the exact file paths to review (codex reads the workspace directly
via --cd; the opus reviewer reads the same paths with its own tools)>
ACTIVE DIRECTIVES (acceptance constraints): <the U-ids + quoted MUST/DESIGN directive text
from Comm.md's `## Directives & Memory` whose `Governs` set this task touches. The work must
NOT violate any of these — treat a violation as a failing finding.>
CONNECTIVITY (when a graphify map exists): the post-change graph in `graphify-out/`
(`GRAPH_REPORT.md` for god nodes / import cycles / knowledge gaps, `graph.json` for raw edges) and
the pre-change `## Connectivity Map (Graphify)` snapshot from Comm.md. Reference the
`<workspace>/graphify-out` paths in the prompt; both reviewers read those files directly.

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

- `codex exec` errors, times out (no `R<id>-out.txt` after ~10 min), or produces an
  EMPTY output file → retry once.
- Second failure (or Codex CLI unavailable / not logged in) → log it in Comm.md and
  use the **opus Fallback Reviewer** (a `general-purpose` `opus` worker,
  `run_in_background: true`, given the same review prompt template). Note in the
  Review Log that the review was same-vendor (Claude), so its independence is weaker.
- An unusable response (no VERDICT, off-topic) → treat as a failure, not PASS.

## Escalation

Two consecutive FAIL verdicts on the same task mean the problem is the plan, not
the worker. Leader Claude stops the loop, re-examines the architecture for that
task, and either re-designs it or escalates to the user with the trade-offs.
