# Adoption Guide

## 1. Copy and configure

Preserve `src/cogem`, `scripts`, `skills/cogem`, `.agents`, configuration, and instructions. Configure objective, ignore paths, core paths, and writer limit in `cogem.config.json`.

## 2. Configure runtimes

Load `model-presets/plan-a-gpt-antigravity.env` and keep credentials outside Cogem.

## 3. Create the first Task

Copy `.agents/templates/task.json`. Every Task must explicitly declare `review_level`; Skill paths require `high-risk`.

## 4. Analyze and dispatch

```bash
python scripts/cogem.py skill-check --root .
python scripts/cogem.py graph --root .
python scripts/cogem.py validate --root .
python scripts/cogem.py dispatch-check TASK-NNN --root .
```

The last command records the scope baseline. Do not delete or replace it after work begins.

## 5. Execute and verify scope

Use isolated worktrees for parallel Writers. Before handoff or review:

```bash
python scripts/cogem.py scope-check TASK-NNN --root .
python scripts/cogem.py validate --root .
```

## 6. Create Skills

```bash
python scripts/cogem.py skill-init example-skill --root .
```

Use `--resources` for optional responsibility directories, then author the content, update the manifest in the same Task, and run `skill-check` plus `scope-check`.

## 7. Review and release

Run independent review for all integrated work and a second adversarial pass for high-risk work. Package only from clean bootstrap state, then verify tests, compile checks, Skill policy, graph generation, and validation in a fresh extraction.
