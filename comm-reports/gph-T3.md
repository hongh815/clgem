# gph-T3 — graphify 연동 마켓플레이스 이식 (Implementer/sonnet) 전문

STATUS: success

CHANGED (마켓플레이스 clgem-marketplace\plugins\clgem\skills\clgem\):
1. CREATED references/graphify-integration.md — 설치본 복사 + 명명 1곳 적응:
   "How it pairs with the review gate"의 reviewer를 "(the Gemini CLI reviewer, or the opus Background Reviewer)"로.
   Grep으로 Antigravity/agy 0건 확인.
2. EDITED SKILL.md (가산 삽입 4):
   - Step 1.5 (L73) — Step 2 직전.
   - Step 2 connectivity 분해 문단 (L91-94) — 설계책임 문장 앞.
   - Step 3 "4.5. Verify completeness via graphify" (L121-127) — Decide↔Update goal 사이. `/graphify ... --update`.
   - Finishing 문장 (L177-178).
3. EDITED assets/Comm.template.md — "## Connectivity Map (Graphify)" (L49-59) — Worker Reports↔Gemini Review Log 사이.

EVIDENCE: 모든 삽입 정위치, 기존 Gemini CLI/gemini-review.md/gemini --version 본문 무변경.

CONCERNS (리뷰어 제기): 마켓플레이스엔 Autonomy tiers 표가 없어 Step1.5/참조의 "Autonomy Tier 0"가 댕글링.
LEADER 후처리: 마켓플레이스 SKILL.md Step1.5 + graphify-integration.md 양쪽의 "Autonomy Tier 0" 표현을
"read-mostly reconnaissance ... needs no user confirmation"로 풀어써 댕글링 제거. (설치본은 Autonomy 표가 있어 원문 유지.)
