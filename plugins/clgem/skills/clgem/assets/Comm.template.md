# clgem Agent Communication Ledger — Active State

Workspace: <absolute path of the project>
Session started: <YYYY-MM-DD HH:MM TZ — actual system time, not guessed>
Sole writer: Leader Claude (Fable 5). Workers report via their final message;
Leader transcribes. Append-only — never delete history; original content is
preserved in comm-reports/, comm-index.md, and comm-summary.md.
Timestamp every entry with date **and** time (from the system clock, e.g. `date`);
actively record into comm-index.md / comm-summary.md / comm-reports/ too — not Comm.md alone.

<!-- 3-tier file roles:
  Comm.md         → active session state only (≤ 200 lines). THIS file.
  comm-index.md   → append-only project registry: all tasks, decisions, questions.
  comm-summary.md → Leader-maintained rollup: goals, rationale, Session Resume Checklist.
  comm-reports/   → per-task permanent artifacts (T1.md, T2.md, …).
-->

## /goal

- **Statement**: <one sentence, outcome terms>
- **Acceptance criteria**:
  1. <verifiable criterion>
- **Definition of done**: <closing evidence>
- **Assumptions**: <defaults Leader chose where the request was ambiguous>
- **Completion**: 0%  <!-- = (criteria fully met ÷ total criteria) × 100 -->

## Status Summary

<2-3 lines max: where the project stands right now. MUST end with:
"Next action: <one sentence — what Leader or the next worker will do first on resume.>"
Update on every state change — this is the first thing a resumed session reads.>

## Directives & Memory

<!-- 살아있는 지침·기억 (SKILL.md Step 1.6). 대화 중 사용자가 말한 ① MUST(지켜야 할 제약)
     ② REMEMBER(기억하라는 사실) ③ IMPORTANT(강조한 우선순위) ④ DESIGN(설계 중점 요소)을
     지속 포착해 여기 적는다. /goal·Status Summary와 동급으로 **압축 대상 아님(active만 유지)**.
     전문은 comm-reports/directives.md(graphify 피드 파일, assets/directives.template.md 에서 초기화)에,
     레지스트리는 comm-index.md `## Directives`, 폐기분 근거는 comm-summary.md `## Leader Profile`.
     매 항목 일자+시간(시스템 시계) 표기. directives.md 추가/변경/폐기 시 `/graphify <path> --update`로
     governance 노드 갱신. 폐기 시 삭제하지 말고 directives.md `## Superseded`로 옮겨 live 엣지 중단. -->

| Id | Cat | Directive (1 line) | Source | Governs (resources/tasks) | Graph node | Status |
| --- | --- | --- | --- | --- | --- | --- |
| U1 | MUST/REMEMBER/IMPORTANT/DESIGN | <지침 1줄> | <사용자 발화·일시> | <적용 리소스/태스크> | comm-reports/directives.md → graphify | active |

## Interrupted State

<!-- Include this section ONLY when a session ends with active tasks in flight.
     Remove it at the start of the next session after reviewing it. -->

- **Interrupted at**: <YYYY-MM-DD HH:MM TZ>
- **In-progress tasks**: <T-ids and their last known state>
- **Last worker output summary**: <one sentence per task>
- **Next action on resume**: <what Leader must do first — e.g., "collect T3 report, then run codex review">

## Agent Roster

<!-- Active agents only. Remove rows for roles not active in this loop. -->

| Role | Model | Status | Current task |
| --- | --- | --- | --- |
| Leader Claude | Fable 5 | Active | Orchestration |
| Implementer | sonnet | Standby | — |
| Scout | haiku | Standby | — |
| Mechanic | haiku | Standby | — |
| Codex Reviewer (default·headless) | codex exec / gpt-5.5 (high reasoning) | Standby | — |
| Fallback Reviewer | opus (run_in_background) | Standby | — |

## Task Board

<!-- Current loop tasks only. Completed (done) tasks move to comm-index.md. -->

| Id | Task | Role/Model | Depends on | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| T1 | <description> | Implementer/sonnet | — | todo | |

Status values: `todo` → `in-progress` → `done-pending-review` → `done`
(or `redo` / `blocked`).

## Worker Reports

<!-- Only tasks NOT yet done. CONDENSE worker results to the essentials here
     (STATUS + key CHANGED + load-bearing EVIDENCE + downstream CONCERNS); the full
     report is preserved in comm-reports/T<id>.md. When a task reaches done, remove
     its block from here and add one line to comm-index.md. -->

### T1 — <task title> (<role/model>)
- STATUS: <success | partial | blocked>
- CHANGED: <key files/artifacts only>
- EVIDENCE: <the verification that matters downstream>
- CONCERNS: <risks the reviewer should probe>

## Connectivity Map (Graphify)

<!-- 표준 단계 — graphify 연결성 맵은 기본적으로 전체 경로를 빌드해 채운다(토큰비용 수용·--mode deep, 표준 빌드).
     생략은 (a) 경로에 리소스가 사실상 하나뿐이거나 (b) graphify 미설치(설치 안내했으나 미가용)일 때만이며,
     그 경우에만 생략 사유를 적는다(예: "graph 생략: graphify 미설치 — 설치 안내함"). -->

- **Graph built (path & depth)**: <graphed 경로 + --mode deep 여부 / 드문 예외로 생략 시: single-resource 사유>
- **God nodes (blast radius)**: <core abstractions; 이들을 건드리는 태스크는 직렬화 + 강한 제약>
- **Communities (task seams)**: <클러스터 → 태스크 분해 경계>
- **Surprising connections → constraints**: <숨은 의존성 → Decision Log에 옮긴 설계 제약>
- **Knowledge gaps / isolated nodes (completeness watchlist)**: <누락 의심 노드>
- **Last --update delta**: <변경 후 새 god node/사이클/남은 gap>

## Codex Review Log

<!-- codex reviews are recorded IN FULL, well-organized — never condensed to a bare
     verdict. The table is for at-a-glance scanning; the full verdict + complete
     findings go in the per-review block below it. On done, move the full block to
     comm-summary.md and leave a one-line pointer in comm-index.md. -->

| Id | Task | Verdict | Leader decision |
| --- | --- | --- | --- |
| R1 | T1 | <PASS/CONDITIONAL/FAIL> | <REDO/SUPPLEMENT/ACCEPT> |

### R1 — review of T1 (codex / gpt-5.5 high reasoning)
- **VERDICT**: <PASS | CONDITIONAL | FAIL>
- **FINDINGS** (complete, most severe first):
  1. <finding, kept in full>
- **Leader decision**: <REDO / SUPPLEMENT / ACCEPT> — <full rationale, incl. any
  finding accepted/overridden and why>

## Leader Decision Log

<!-- Keep the 5 most recent entries here. Older entries move to comm-summary.md. -->

- <YYYY-MM-DD HH:MM TZ> — <architecture/design decision and why; workers and reviews reference this>
  - **next_action**: <task to spawn next loop, or "none">

## Open Items

- <unresolved questions, deferred findings, follow-ups>
