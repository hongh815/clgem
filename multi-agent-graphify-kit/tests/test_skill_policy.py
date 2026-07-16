import json
import tempfile
import unittest
from pathlib import Path

from cogem.skill_policy import (
    SkillPolicyError,
    load_skill_manifest,
    parse_skill_frontmatter,
    validate_skills,
)


class SkillPolicyTests(unittest.TestCase):
    def _skill(self, root: Path, name: str = "demo-skill", *, description: str = "Use when a demo skill is required.") -> Path:
        skill = root / "skills" / name
        (skill / "references").mkdir(parents=True)
        (skill / "schemas").mkdir()
        (skill / "scripts").mkdir()
        (skill / "tests").mkdir()
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n# Demo\n",
            encoding="utf-8",
        )
        (skill / "references" / "guide.md").write_text("# Guide\n", encoding="utf-8")
        (skill / "schemas" / "contract.schema.json").write_text(
            json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"}) + "\n",
            encoding="utf-8",
        )
        (skill / "scripts" / "tool.py").write_text("print('ok')\n", encoding="utf-8")
        (skill / "tests" / "scenario.md").write_text("# Scenario\n", encoding="utf-8")
        entries = [
            "SKILL.md",
            "manifest.txt",
            "references/guide.md",
            "schemas/contract.schema.json",
            "scripts/tool.py",
            "tests/scenario.md",
        ]
        (skill / "manifest.txt").write_text("\n".join(entries) + "\n", encoding="utf-8")
        return skill

    def test_valid_skill_directory_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._skill(root)
            self.assertEqual(validate_skills(root), [])

    def test_codex_agents_and_assets_directories_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = self._skill(root)
            (skill / "agents").mkdir()
            (skill / "assets").mkdir()
            (skill / "agents" / "openai.yaml").write_text("interface:\n  display_name: Demo\n", encoding="utf-8")
            (skill / "assets" / "template.txt").write_text("template\n", encoding="utf-8")
            manifest = (skill / "manifest.txt").read_text(encoding="utf-8")
            (skill / "manifest.txt").write_text(
                manifest + "agents/openai.yaml\nassets/template.txt\n",
                encoding="utf-8",
            )
            self.assertEqual(validate_skills(root), [])

    def test_optional_skill_root_entries_must_be_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = self._skill(root)
            (skill / "assets").write_text("not a directory\n", encoding="utf-8")
            (skill / "manifest.txt").write_text(
                "SKILL.md\nmanifest.txt\nassets\n",
                encoding="utf-8",
            )
            issues = validate_skills(root)
            self.assertIn("SKILL_ROOT_ENTRY_TYPE", [issue.code for issue in issues])

    def test_skill_name_may_be_63_characters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._skill(root, name="a" * 63)
            self.assertEqual(validate_skills(root), [])

    def test_skill_name_must_be_shorter_than_64_characters(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._skill(root, name="a" * 64)
            codes = {issue.code for issue in validate_skills(root)}
            self.assertIn("SKILL_DIRECTORY_NAME", codes)

    def test_frontmatter_rejects_fields_other_than_name_and_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = self._skill(root)
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            text = text.replace("description: Use when a demo skill is required.\n", "description: Use when a demo skill is required.\nversion: 1\n")
            (skill / "SKILL.md").write_text(text, encoding="utf-8")
            codes = {issue.code for issue in validate_skills(root)}
            self.assertIn("SKILL_FRONTMATTER_INVALID", codes)

    def test_frontmatter_rejects_multiline_yaml_scalars_explicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = self._skill(root)
            (skill / "SKILL.md").write_text(
                "---\nname: demo-skill\ndescription: >\n  Use when a demo skill is required.\n---\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SkillPolicyError, "single-line scalar"):
                parse_skill_frontmatter(skill / "SKILL.md")

    def test_name_must_match_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = self._skill(root)
            text = (skill / "SKILL.md").read_text(encoding="utf-8").replace("name: demo-skill", "name: other")
            (skill / "SKILL.md").write_text(text, encoding="utf-8")
            codes = {issue.code for issue in validate_skills(root)}
            self.assertIn("SKILL_NAME_MISMATCH", codes)

    def test_description_must_start_with_use_when(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._skill(root, description="Coordinates demo work.")
            codes = {issue.code for issue in validate_skills(root)}
            self.assertIn("SKILL_DESCRIPTION_TRIGGER", codes)

    def test_manifest_rejects_unlisted_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = self._skill(root)
            (skill / "references" / "unlisted.md").write_text("# Hidden\n", encoding="utf-8")
            codes = {issue.code for issue in validate_skills(root)}
            self.assertIn("SKILL_UNLISTED_FILE", codes)

    def test_manifest_rejects_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = self._skill(root)
            (skill / "scripts" / "tool.py").unlink()
            codes = {issue.code for issue in validate_skills(root)}
            self.assertIn("SKILL_MANIFEST_MISSING_FILE", codes)

    def test_manifest_must_include_itself_and_skill_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = self._skill(root)
            (skill / "manifest.txt").write_text("references/guide.md\n", encoding="utf-8")
            codes = {issue.code for issue in validate_skills(root)}
            self.assertIn("SKILL_MANIFEST_REQUIRED_ENTRY", codes)

    def test_manifest_paths_cannot_escape_skill_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = self._skill(root)
            (skill / "manifest.txt").write_text("SKILL.md\nmanifest.txt\n../outside.md\n", encoding="utf-8")
            with self.assertRaises(SkillPolicyError):
                load_skill_manifest(skill)

    def test_invalid_schema_json_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = self._skill(root)
            (skill / "schemas" / "contract.schema.json").write_text("{", encoding="utf-8")
            codes = {issue.code for issue in validate_skills(root)}
            self.assertIn("SKILL_SCHEMA_INVALID_JSON", codes)


if __name__ == "__main__":
    unittest.main()
