# clgem Agent Communication Ledger

Workspace: <absolute path of the project>
Session started: <date>
Sole writer: Leader Claude (Fable 5). Workers report via their final message;
Leader transcribes. Append-only — never delete history.

## /goal

- **Statement**: <one sentence, outcome terms>
- **Acceptance criteria**:
  1. <verifiable criterion>
- **Definition of done**: <closing evidence>
- **Assumptions**: <defaults Leader chose where the request was ambiguous>
- **Completion**: 0%  <!-- = (criteria fully met ÷ total criteria) × 100 -->

## Status Summary

<2-3 lines: where the project stands right now. Update on every state change —
this is the first thing a resumed session or the user reads.>

## Agent Roster

| Role | Model | Status | Current task |
| --- | --- | --- | --- |
| Leader Claude | Fable 5 | Active | Orchestration |
| Implementer | sonnet | Standby | — |
| Scout | haiku | Standby | — |
| Mechanic | haiku | Standby | — |
| Gemini Reviewer | Gemini CLI | Standby | — |

## Task Board

| Id | Task | Role/Model | Depends on | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| T1 | <description> | Implementer/sonnet | — | todo | |

Status values: `todo` → `in-progress` → `done-pending-review` → `done`
(or `redo` / `blocked`).

## Worker Reports

### T1 — <task title>
- STATUS: <success | partial | blocked>
- CHANGED: <files/artifacts>
- EVIDENCE: <verification performed>
- CONCERNS: <risks the reviewer should probe>

## Gemini Review Log

| Id | Task | Verdict | Key findings | Leader decision | Justification |
| --- | --- | --- | --- | --- | --- |
| R1 | T1 | <PASS/CONDITIONAL/FAIL> | <condensed> | <REDO/SUPPLEMENT/ACCEPT> | <one line> |

## Leader Decision Log

- <date> — <architecture/design decision and why; workers and reviews reference this>

## Open Items

- <unresolved questions, deferred findings, follow-ups>

## Archive

<move stale sections here when the file grows unwieldy>
