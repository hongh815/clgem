# Graph Report - .  (2026-06-20)

## Corpus Check
- Corpus is ~12,081 words - fits in a single context window. You may not need a graph.

## Summary
- 56 nodes · 73 edges · 9 communities
- Extraction: 70% EXTRACTED · 30% INFERRED · 0% AMBIGUOUS · INFERRED: 22 edges (avg confidence: 0.88)
- Token cost: 106,602 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Agent Roster & Orchestration|Agent Roster & Orchestration]]
- [[_COMMUNITY_Gemini Review Gate|Gemini Review Gate]]
- [[_COMMUNITY_Weather Dashboard App|Weather Dashboard App]]
- [[_COMMUNITY_Teammate-Gap & Persistent Store|Teammate-Gap & Persistent Store]]
- [[_COMMUNITY_Antigravity CLI Review Runners|Antigravity CLI Review Runners]]
- [[_COMMUNITY_Comm.md Ledger & Discipline|Comm.md Ledger & Discipline]]

## God Nodes (most connected - your core abstractions)
1. `clgem SKILL — Leader Claude Multi-Agent Orchestration` - 7 edges
2. `T2 Teammate Gap Analysis Report` - 7 edges
3. `WeatherAPIClient` - 7 edges
4. `clgem Agent Roster — Roles and Model Assignment` - 6 edges
5. `Three-Tier Persistent Store (Comm/index/summary)` - 6 edges
6. `Independent Critical Reviewer (Gemini)` - 5 edges
7. `DashboardUI (React)` - 5 edges
8. `Antigravity CLI (agy, Gemini 3.1 Pro High)` - 4 edges
9. `Gemini CLI critical review gate` - 4 edges
10. `Review Verdict (PASS/CONDITIONAL/FAIL)` - 4 edges

## Surprising Connections (you probably didn't know these)
- `Antigravity CLI (agy, Gemini 3.1 Pro High)` --semantically_similar_to--> `Gemini CLI critical review gate`  [INFERRED] [semantically similar]
  comm-reports/R1-run.ps1 → clgem-marketplace/plugins/clgem/skills/clgem/SKILL.md
- `R1 review runner (agy non-interactive capture)` --implements--> `Gemini CLI critical review gate`  [INFERRED]
  comm-reports/R1-run.ps1 → clgem-marketplace/plugins/clgem/skills/clgem/SKILL.md
- `R3 interactive review runner (agy)` --implements--> `Dual independent review (opus background + agy interactive)`  [INFERRED]
  comm-reports/R3-run.ps1 → Comm.md
- `TTY transcript test runner` --conceptually_related_to--> `agy non-interactive output capture impossible (TTY-only)`  [INFERRED]
  comm-reports/ttytest-run.ps1 → Comm.md
- `clgem plugin manifest` --references--> `clgem SKILL — Leader Claude Multi-Agent Orchestration`  [INFERRED]
  clgem-marketplace/plugins/clgem/.claude-plugin/plugin.json → clgem-marketplace/plugins/clgem/skills/clgem/SKILL.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **clgem orchestration: Leader, workers, review gate, ledger** — clgem_leader_claude, clgem_execution_loop, clgem_gemini_review, clgem_commmd_discipline [EXTRACTED 0.85]
- **agy review runner scripts probing TTY capture** — r1_run_review, r3_run_review, ttytest_run, comm_agy_capture_limit [INFERRED 0.75]
- **Weather Dashboard Component Data Flow** — comm_reports_t3_dashboardui, comm_reports_t1_weatherapiclient, comm_reports_t2_cachestore, comm_reports_t1_openweather_api [EXTRACTED 1.00]
- **Three-Tier Persistent Store Layout** — sample_store_comm_ledger, sample_store_comm_index, sample_store_comm_summary [INFERRED 0.85]
- **Gemini Review Gate Decision Flow** — references_gemini_review_independent_reviewer, references_gemini_review_verdict, references_gemini_review_leader_decision, references_gemini_review_comm_log [EXTRACTED 1.00]

## Communities (9 total, 0 thin omitted)

### Community 0 - "Agent Roster & Orchestration"
Cohesion: 0.24
Nodes (11): Implementer role (sonnet), clgem Agent Roster — Roles and Model Assignment, Scout role (haiku), Token economy model-selection principle, Step 3 Execution loop, Leader Claude (Fable 5 / Opus 4.8 fallback), clgem SKILL — Leader Claude Multi-Agent Orchestration, Worker prompt template (REPORT FORMAT) (+3 more)

### Community 1 - "Gemini Review Gate"
Cohesion: 0.24
Nodes (10): R1 Review Prompt (T2 teammate gap), R1b Review Prompt (T2 full report), R3 Review Prompt (T3+T4 implementation), Comm.md Gemini Review Log, FAIL Escalation (re-design plan), Fallback Reviewer (opus worker), Independent Critical Reviewer (Gemini), Leader Decision (REDO/SUPPLEMENT/ACCEPT) (+2 more)

### Community 2 - "Weather Dashboard App"
Cohesion: 0.33
Nodes (9): ConfigLoader, OpenWeather API, RetryPolicy (exponential backoff), WeatherAPIClient, CacheStore (Redis, 5min TTL), Redis, DashboardUI (React), WeatherCard (+1 more)

### Community 3 - "Teammate-Gap & Persistent Store"
Cohesion: 0.36
Nodes (9): Autonomy Tier + Committed Action, Selective Loading / Resume Protocol, Session Checkpoint + Interrupted State, Six-Axis Teammate Gap Framework, T2 Teammate Gap Analysis Report, Three-Tier Persistent Store (Comm/index/summary), sample-store Project Index, sample-store Comm.md Ledger (+1 more)

### Community 4 - "Antigravity CLI Review Runners"
Cohesion: 0.38
Nodes (7): Fallback Reviewer role (opus), Antigravity CLI (agy, Gemini 3.1 Pro High), Gemini CLI critical review gate, agy non-interactive output capture impossible (TTY-only), opus Fallback Reviewer decision, R1 review runner (agy non-interactive capture), TTY transcript test runner

### Community 5 - "Comm.md Ledger & Discipline"
Cohesion: 0.29
Nodes (7): Comm.md discipline (sole writer, append-only), Dual independent review (opus background + agy interactive), Teammate-ization /goal, clgem Agent Communication Ledger (Comm.md), Comm.md template, Three-tier persistent storage design, R3 interactive review runner (agy)

## Knowledge Gaps
- **10 isolated node(s):** `clgem plugin (README description)`, `Implementer role (sonnet)`, `Scout role (haiku)`, `FAIL Escalation (re-design plan)`, `Comm.md Gemini Review Log` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Three-Tier Persistent Store (Comm/index/summary)` connect `Teammate-Gap & Persistent Store` to `Gemini Review Gate`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Why does `clgem SKILL — Leader Claude Multi-Agent Orchestration` connect `Agent Roster & Orchestration` to `Comm.md Ledger & Discipline`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Why does `T2 Teammate Gap Analysis Report` connect `Teammate-Gap & Persistent Store` to `Gemini Review Gate`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Three-Tier Persistent Store (Comm/index/summary)` (e.g. with `sample-store Project Index` and `sample-store Comm.md Ledger`) actually correct?**
  _`Three-Tier Persistent Store (Comm/index/summary)` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `clgem plugin (README description)`, `Implementer role (sonnet)`, `Scout role (haiku)` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._