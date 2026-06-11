# clgem Gemini Review Gate

This file replaces the Codex-era `Codex_Gemini_Agent_Strategy.md`. In clgem the
Gemini review is **not optional** — every completed task passes through it before
Leader Claude marks it done. An independent model catches what a same-model
reviewer rationalizes away; that independence is the point of paying for the
extra session.

## Invocation

Run the Gemini CLI in non-interactive print mode as a separate session via Bash:

```powershell
gemini -p "<review prompt>"
```

For long prompts, write the review prompt to a temp file and pipe it:

```powershell
Get-Content review-prompt.txt -Raw | gemini
```

Reviews of a finished task may run with `run_in_background: true` while the next
task executes — Leader Claude collects the verdict when it arrives. Do not let
more than two unreviewed tasks accumulate, or a bad early task contaminates work
built on top of it.

## Review prompt template

Give Gemini everything it needs to be genuinely critical — the goal, the claim,
and the evidence — and explicitly license it to fail the work:

```
You are an independent critical reviewer. Your job is to find what is wrong,
missing, or divergent from the goal — not to be agreeable. If you cannot verify
a claim, say so.

PROJECT GOAL: <the /goal statement and acceptance criteria>
TASK <id>: <what the worker was asked to do>
WORKER REPORT: <the worker's STATUS/CHANGED/EVIDENCE/CONCERNS block>
ARTIFACTS: <relevant file contents or diff — paste the actual content;
Gemini cannot read the workspace itself>

Review for: correctness, missing edge cases, divergence from the goal,
unverified claims in the report, and risks the worker did not mention.

End with exactly:
VERDICT: PASS | CONDITIONAL | FAIL
FINDINGS: <numbered list, most severe first>
```

Paste real artifact content into the prompt — a review of a summary is a summary
of a review.

## Logging and the Leader decision

Log every review in Comm.md's Gemini Review Log: review id (`R1`, `R2`, …),
target task id, verdict, key findings (condensed), and then the Leader decision —
**REDO / SUPPLEMENT / ACCEPT** — with a one-line justification. The justification
is mandatory for ACCEPT-despite-findings: an ignored finding without a recorded
reason is indistinguishable from an overlooked one.

Findings feed forward: when a task is reassigned (REDO) or extended
(SUPPLEMENT), attach the relevant findings verbatim to the new worker prompt.

## Failure handling

- Gemini call errors or times out → retry once.
- Second failure → log it in Comm.md and use the **Fallback Reviewer** (an `opus`
  worker agent given the same review prompt template). Note in the Review Log
  that the review was same-vendor, so its independence is weaker.
- Gemini returns an unusable response (no verdict, off-topic) → treat as a
  failure, not a PASS.

## Escalation

Two consecutive FAIL verdicts on the same task mean the problem is the plan, not
the worker. Leader Claude stops the loop, re-examines the architecture for that
task, and either re-designs it or escalates to the user with the trade-offs.
