"""Non-interactive scaffolding for strict Cogem Skill directories."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Iterable

from .skill_policy import SkillPolicyError, validate_skill_name, validate_skills


_ALLOWED_RESOURCES = {"references", "scripts", "assets", "schemas", "tests"}
_RESOURCE_ALIASES = {"schemes": "schemas"}


def normalize_resources(values: Iterable[str]) -> tuple[str, ...]:
    """Normalize, validate, and deduplicate requested Skill resource directories."""

    normalized: list[str] = []
    for raw in values:
        for part in str(raw).split(","):
            value = part.strip().lower()
            if not value:
                continue
            value = _RESOURCE_ALIASES.get(value, value)
            if value not in _ALLOWED_RESOURCES:
                allowed = ", ".join(sorted(_ALLOWED_RESOURCES))
                raise SkillPolicyError(f"unsupported Skill resource {value!r}; expected one of {allowed}")
            if value not in normalized:
                normalized.append(value)
    return tuple(normalized)


def _display_name(name: str) -> str:
    return " ".join(token.capitalize() for token in name.split("-"))


def initialize_skill(root: Path, name: str, resources: Iterable[str] = ()) -> Path:
    """Create a minimal Codex-compatible Skill and immediately validate it."""

    root = Path(root).resolve()
    valid_name = validate_skill_name(name)
    selected = normalize_resources(resources)
    skill_dir = root / "skills" / valid_name
    if skill_dir.exists():
        raise SkillPolicyError(f"Skill already exists: skills/{valid_name}")

    created_skills_root = not (root / "skills").exists()
    try:
        (skill_dir / "agents").mkdir(parents=True)
        for resource in selected:
            (skill_dir / resource).mkdir()

        description = f"Use when tasks require {valid_name}-specific guidance."
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            f"name: {valid_name}\n"
            f"description: {description}\n"
            "---\n\n"
            f"# {_display_name(valid_name)}\n\n"
            "## Overview\n\n"
            f"Use this Skill as the operating guide for `{valid_name}` work.\n",
            encoding="utf-8",
        )
        (skill_dir / "agents" / "openai.yaml").write_text(
            "interface:\n"
            f"  display_name: {_display_name(valid_name)}\n"
            f"  short_description: Guidance for {valid_name} tasks.\n",
            encoding="utf-8",
        )
        (skill_dir / "manifest.txt").write_text(
            "SKILL.md\nmanifest.txt\nagents/openai.yaml\n",
            encoding="utf-8",
        )

        issues = validate_skills(root)
        if issues:
            details = "; ".join(f"{issue.code} [{issue.path}]: {issue.message}" for issue in issues)
            raise SkillPolicyError(f"skill-check failed after initialization: {details}")
        return skill_dir
    except Exception:
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
        skills_root = root / "skills"
        if created_skills_root and skills_root.exists() and not any(skills_root.iterdir()):
            skills_root.rmdir()
        raise
