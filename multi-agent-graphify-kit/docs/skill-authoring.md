# Skill Authoring Policy

This is the canonical project-level policy for creating, modifying, validating, and distributing Skills.

## 1. Skill file contract

Each Skill is a directory at `skills/<skill-name>/`. Names contain 1–63 lowercase letters, numbers, or hyphen-separated tokens.

Required files:

```text
SKILL.md
manifest.txt
```

Allowed root entries are exactly:

```text
SKILL.md
manifest.txt
agents/
assets/
references/
scripts/
schemas/
tests/
```

Every optional root entry is a directory, not a same-named file.

`agents/openai.yaml` is recommended but not required for manually authored Skills. `cogem skill-init` creates it by default. `assets/` holds distributable templates, images, or other output resources. Every file in every allowed directory remains subject to `manifest.txt`.

## 2. Exact frontmatter contract

`SKILL.md` starts with exactly two frontmatter fields:

```yaml
---
name: example-skill
description: Use when concrete activation conditions apply.
---
```

Rules:

- no fields other than `name` and `description`;
- directory name and `name` are identical;
- `description` starts with `Use when` and describes activation conditions rather than the workflow;
- both values use single-line scalar syntax.

Cogem intentionally uses a lightweight parser and does not support YAML block scalars, folded values, lists, mappings, anchors, or multi-line frontmatter values.

## 3. Manifest authority

Every distributable Skill file appears once in `manifest.txt`, relative to the Skill directory. The manifest includes itself and `SKILL.md`.

Entries must not be absolute, traverse parents, duplicate another entry, point to a missing file, or omit an existing file. Packaging stops on any drift.

## 4. Controlled modification procedure

Skill paths are critical. `review_level` is required in every Task contract, and any Task whose `write_set` includes `skills` or a descendant must use `high-risk`. Both `dispatch-check` and `validate` enforce this as `SKILL_REVIEW_LEVEL_REQUIRED`.

Before work:

```bash
python scripts/cogem.py skill-check --root .
python scripts/cogem.py graph --root .
python scripts/cogem.py validate --root .
python scripts/cogem.py dispatch-check TASK-NNN --root .
```

The successful dispatch records the baseline used by scope verification.

During work, modify only `write_set`. If a Skill file is created, changed, deleted, or renamed, change that Skill’s `manifest.txt` in the same Task.

Before handoff or review:

```bash
python scripts/cogem.py skill-check --root .
python scripts/cogem.py scope-check TASK-NNN --root .
python scripts/run_tests.py
python -m compileall -q src scripts skills/cogem/scripts
python scripts/cogem.py graph --root .
python scripts/cogem.py validate --root .
```

## 5. Skill initialization

```bash
python scripts/cogem.py skill-init example-skill --root .
python scripts/cogem.py skill-init example-skill \
  --resources references,scripts,assets,schemas,tests \
  --root .
```

The basic product is:

```text
skills/example-skill/
├── SKILL.md
├── manifest.txt
└── agents/
    └── openai.yaml
```

The command rejects invalid names and existing directories, creates requested resource directories, runs the same generic Skill check, and rolls back the new Skill if validation fails. `schemes` is accepted as an alias for `schemas`.

## 6. Review requirements

Every Skill change requires:

1. fresh-context, read-only independent Antigravity review;
2. separate fresh-context adversarial Antigravity review;
3. both reports bound to the same Task `review_tree_hash`;
4. `prior_findings_provided: false` for the adversarial pass.
