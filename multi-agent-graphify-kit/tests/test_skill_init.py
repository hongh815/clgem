import tempfile
import unittest
from pathlib import Path

from cogem.skill_init import initialize_skill, normalize_resources
from cogem.skill_policy import SkillPolicyError, validate_skills


class SkillInitTests(unittest.TestCase):
    def test_basic_skill_contains_skill_manifest_and_openai_agent_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = initialize_skill(root, "example-skill", ())
            self.assertTrue((skill / "SKILL.md").is_file())
            self.assertTrue((skill / "manifest.txt").is_file())
            self.assertTrue((skill / "agents" / "openai.yaml").is_file())
            self.assertEqual(validate_skills(root), [])
            self.assertEqual(
                (skill / "manifest.txt").read_text(encoding="utf-8").splitlines(),
                ["SKILL.md", "manifest.txt", "agents/openai.yaml"],
            )

    def test_optional_resource_directories_are_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = initialize_skill(
                root,
                "resource-skill",
                ("references", "scripts", "assets", "schemas", "tests"),
            )
            for name in ("references", "scripts", "assets", "schemas", "tests"):
                self.assertTrue((skill / name).is_dir())
            self.assertEqual(validate_skills(root), [])

    def test_schemes_is_normalized_to_schemas(self):
        self.assertEqual(normalize_resources(["references", "schemes"]), ("references", "schemas"))

    def test_invalid_name_is_rejected_without_creating_a_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(SkillPolicyError):
                initialize_skill(root, "Invalid_Name", ())
            self.assertFalse((root / "skills").exists())

    def test_existing_skill_name_conflict_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initialize_skill(root, "example-skill", ())
            with self.assertRaisesRegex(SkillPolicyError, "already exists"):
                initialize_skill(root, "example-skill", ())


if __name__ == "__main__":
    unittest.main()
