# Cogem Execution Engine Presets

## Plan A: GPT implementation and Antigravity review

`plan-a-gpt-antigravity.env` is the recommended allocation when GPT and Google Antigravity are the available runtimes.

| Role | Exact runtime model or managed agent | Deliberation | Required |
| --- | --- | --- | ---: |
| Coordinator | `gpt-5.6-sol` | `max` | Yes |
| Graph Analyst | `gpt-5.6-terra` | `high` | Yes |
| Worker A | `gpt-5.6-terra` | `high` | Yes |
| Worker B | `gpt-5.6-terra` | `high` | Yes |
| Independent Reviewer | `antigravity-preview-05-2026` | Managed by the runtime | Yes |

The Independent Reviewer is the only permanent review role. It always starts in a fresh context with read-only project access and receives requirements, the integrated tree, diff, Cogem graph, task contracts, and verification evidence—not worker conversation history.

For high-risk changes, launch a **high-risk second pass** as a second fresh Independent Reviewer session using the same Antigravity runtime and an adversarial brief. Do not reuse the first review context or create another permanent role.

Load and verify the preset:

```bash
set -a
. model-presets/plan-a-gpt-antigravity.env
set +a
python scripts/cogem.py engine-plan --root . --require-resolved --show-engine-ids
python scripts/cogem.py validate --root . --require-engines
```

## Emergency GPT-only degraded mode

The preset records `gpt-5.6-sol` as the emergency review fallback but leaves it disabled:

```dotenv
COGEM_REVIEW_FALLBACK_ENGINE=gpt-5.6-sol
COGEM_ALLOW_DEGRADED_REVIEW=false
```

When Antigravity is unavailable, a Coordinator may explicitly set `COGEM_ALLOW_DEGRADED_REVIEW=true`. Cogem then resolves a fresh, read-only `gpt-5.6-sol` review session and marks it `degraded_independence: true`. This is not equivalent to cross-runtime review and must be recorded in `.agents/reports/`. Cogem never enables it silently.
