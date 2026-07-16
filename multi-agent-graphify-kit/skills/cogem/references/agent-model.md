# Cogem Agent Execution Engine Reference

## Capability profiles

Tasks identify roles, not provider runtimes. `agent-models.json` assigns each role a profile; environment variables contain the actual model or managed-agent ID.

| Profile | Intended use | Plan A recommendation |
| --- | --- | --- |
| `reasoning-high` | Coordinator planning, cross-file integration, difficult decisions | `gpt-5.6-sol` |
| `balanced` | Graph analysis and scoped implementation | `gpt-5.6-terra` |
| `review-high` | Independent consistency, correctness, and adversarial review | `antigravity-preview-05-2026` |

Load `model-presets/plan-a-gpt-antigravity.env` for the exact mapping. Apply `max` deliberation to the Coordinator and `high` to Graph Analyst and Workers. The Antigravity managed agent controls its own deliberation.

## Required isolation

The Independent Reviewer uses `fresh_context: true`, `permissions: read-only`, and a primary engine distinct from all implementation roles. It receives requirements, the integrated tree, diff, graph artifacts, task contracts, and verification evidence. It does not receive worker conversation history.

## High-risk second pass

For high-risk work, launch the same `independent-reviewer` role in a second fresh Antigravity session with an adversarial brief. Do not create another permanent reviewer role, reuse the first review context, or provide the first reviewer's conclusions before the second session reports.

## Missing reviewer engine

Fail required engine resolution when `COGEM_REVIEW_ENGINE` is unset and degraded review is disabled. Do not silently reuse `gpt-5.6-terra`. The explicit fallback uses `COGEM_REVIEW_FALLBACK_ENGINE` only when `COGEM_ALLOW_DEGRADED_REVIEW=true`, and the result must be reported as degraded independence.

## Runtime boundary

Cogem validates allocation policy but does not create agent sessions, set provider-specific reasoning parameters, or call model APIs. The external runtime must apply the selected engine, context isolation, filesystem permissions, and deliberation level.
