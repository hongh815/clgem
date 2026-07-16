# Cogem Command Reference

```bash
python scripts/cogem.py goal-init GOAL-NNN --objective "OUTCOME" --criterion "SUCCESS" --root PROJECT
python scripts/cogem.py goal-check GOAL-NNN --root PROJECT
python scripts/cogem.py skill-init NAME --root PROJECT [--resources LIST]
python scripts/cogem.py skill-check --root PROJECT [--json]
python scripts/cogem.py graph --root PROJECT
python scripts/cogem.py sync --root PROJECT
python scripts/cogem.py validate --root PROJECT [--require-engines] [--json]
python scripts/cogem.py dispatch-check TASK-NNN --root PROJECT
python scripts/cogem.py scope-check TASK-NNN --root PROJECT
python scripts/cogem.py parallel TASK-A TASK-B --root PROJECT
python scripts/cogem.py review-hash --root PROJECT
python scripts/cogem.py engine-plan --root PROJECT [--require-resolved] [--show-engine-ids]
python scripts/cogem.py all --root PROJECT [--require-engines]
```

`skill-init --resources` accepts `references,scripts,assets,schemas,tests`; `schemes` aliases `schemas`. Compatibility aliases remain `model-plan`, `--show-model-ids`, and `--require-models`.

| Exit | Meaning |
| ---: | --- |
| `0` | Success, authorized, scope-compliant, or parallel-safe |
| `1` | General validation failure |
| `2` | Configuration, contract, Skill policy, or engine-policy error |
| `3` | Broken local Markdown link |
| `4` | Dependency cycle |
| `5` | Unsafe parallel pair |
| `6` | Dispatch blocked |
| `7` | Actual changes violate Task scope |
