# Cogem Agent Execution Engine Policy

## Separation of role and runtime identity

Cogem separates **role identity** from **runtime identity**. Task contracts name roles; `agent-models.json` maps each role to a capability profile; environment variables map profiles to a concrete model or managed-agent identifier. The repository remains portable while `model-presets/plan-a-gpt-antigravity.env` records the exact recommended Plan A allocation.

The filename `agent-models.json` and the hidden `model-plan` command are retained for compatibility. New configuration and documentation use **execution engine** because Antigravity is a managed agent rather than an ordinary model.

## Recommended Plan A allocation

| Role | Profile | Exact engine | Deliberation | Permanent |
| --- | --- | --- | --- | ---: |
| Coordinator | `reasoning-high` | `gpt-5.6-sol` | `max` | Yes |
| Graph Analyst | `balanced` | `gpt-5.6-terra` | `high` | Yes |
| Worker A | `balanced` | `gpt-5.6-terra` | `high` | Yes |
| Worker B | `balanced` | `gpt-5.6-terra` | `high` | Yes |
| Independent Reviewer | `review-high` | `antigravity-preview-05-2026` | Managed by runtime | Yes |

There is no separate permanent Antigravity review role. Antigravity executes the required `independent-reviewer` role.

## Environment mapping

```dotenv
COGEM_COORDINATOR_ENGINE=gpt-5.6-sol
COGEM_BALANCED_ENGINE=gpt-5.6-terra
COGEM_REVIEW_ENGINE=antigravity-preview-05-2026
COGEM_REVIEW_FALLBACK_ENGINE=gpt-5.6-sol
COGEM_ALLOW_DEGRADED_REVIEW=false
```

Load the supplied preset:

```bash
set -a
. model-presets/plan-a-gpt-antigravity.env
set +a
```

Cogem treats engine values as opaque runtime identifiers and never uses them as credentials.

## Context and permission isolation

The Independent Reviewer must have:

- `fresh_context: true`;
- `permissions: read-only`;
- a primary engine distinct from Coordinator, Graph Analyst, Worker A, and Worker B;
- no worker conversation history;
- access to approved requirements, the integrated tree, diff, graph artifacts, task contracts, and fresh verification evidence.

The included policy enforces engine diversity by comparing resolved identifiers. It cannot configure provider sandboxes itself; the external agent runtime must apply filesystem permissions and session isolation.

## High-risk second pass

Changes to role authority, schemas, orchestration, security boundaries, release-critical behavior, or broad core paths require a high-risk second pass.

The pass is:

- the same `independent-reviewer` role;
- the same `antigravity-preview-05-2026` engine;
- a new, isolated session;
- a separate adversarial brief;
- independent of the first reviewer's private conversation and conclusions.

This adds another independent attempt without adding a sixth permanent role.

## Missing Antigravity

Cogem does not silently fall back from Antigravity to an implementation engine. With `COGEM_ALLOW_DEGRADED_REVIEW=false`, unresolved `COGEM_REVIEW_ENGINE` causes `--require-engines` and `--require-resolved` to fail.

An emergency GPT-only configuration may set `COGEM_ALLOW_DEGRADED_REVIEW=true`. The policy then uses `COGEM_REVIEW_FALLBACK_ENGINE`, which is `gpt-5.6-sol` in the supplied preset, and marks the resolution as degraded independence. The reviewer still needs a fresh, read-only session. The Coordinator must record the downgrade in a decision and report.

## Inspection and validation

Inspect the role plan without exposing credentials:

```bash
python scripts/cogem.py engine-plan --root .
```

Require every permanent role to resolve and display configured engine IDs:

```bash
python scripts/cogem.py engine-plan --root . --require-resolved --show-engine-ids
python scripts/cogem.py validate --root . --require-engines
```

`model-plan`, `--show-model-ids`, and `--require-models` remain compatibility aliases. Cogem never reads API keys, creates provider sessions, sets provider-specific reasoning parameters, or sends model requests.
