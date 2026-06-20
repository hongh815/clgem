# gph-T2 — graphify 연동 구현 (Implementer/sonnet) 전문

STATUS: success

CHANGED:
1. CREATED `~/.claude/skills/clgem/references/graphify-integration.md` — 조건부 게이트 + 계획단계 사용 +
   완성도체크 사용 + 리뷰게이트 페어링 + 비용/정직성 규칙.
2. EDITED `~/.claude/skills/clgem/SKILL.md`:
   - (2a) `## Step 1.5 — Build the connectivity map (when token-justified)` 를 `## Step 2` 직전 삽입(L108).
   - (2b) "If a connectivity map was built in Step 1.5…" 문단을 "Design the architecture yourself…" 직전(L126).
   - (2c) `5a. Verify completeness via graphify` 를 `5. Update the goal` 직전(L173).
   - (2d) Finishing에 connectivity 완성도 = closing evidence 문장 추가(L380).
3. EDITED `~/.claude/skills/clgem/references/agents.md` — "## Worker conduct" 끝에 Connectivity map(graphify) 문단.
4. EDITED `~/.claude/skills/clgem/assets/Comm.template.md` — `## Connectivity Map (Graphify)` 를
   Worker Reports↔Antigravity Review Log 사이 삽입.

EVIDENCE: 각 삽입이 지정 앵커에 정확히 위치(L108/126/173/380, agents 47-51, template 78-87). 새 파일 모든 섹션 존재.

CONCERNS (Implementer 제기):
- 5a 불릿이 4번(REDO/SUPPLEMENT/ACCEPT) 하위 들여쓰기로 들어가 4번째 결정옵션처럼 읽힐 수 있음.
  → **Leader가 직접 교정**: 5a를 column 0 상위 단계로 dedent(4번 하위 아님, 5번 직전 독립 단계). 해결됨.
- 마켓플레이스 사본 미변경(T3 처리). 기존 Step 본문 재작성 없음(가산 삽입만).

LEADER 후처리: 5a 들여쓰기 교정 적용. 그 외 삽입은 검증 통과.
