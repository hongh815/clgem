import tempfile
import unittest
import zipfile
from pathlib import Path
import shutil
import os
import subprocess
import sys

from scripts.package_kit import ManifestError, create_archive


class PackageTests(unittest.TestCase):
    def test_archive_is_portable_and_excludes_transient_files(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "multi-agent-graphify-kit"
            shutil.copytree(
                source,
                root,
                ignore=shutil.ignore_patterns(".graph", "__pycache__", "*.pyc", "*.pyo", "*.zip"),
            )
            for name in ("tasks", "messages", "decisions", "handoffs", "reports", "snapshots"):
                for record in (root / ".agents" / name).glob("*.json"):
                    record.unlink()
            destination = Path(tmp) / "kit.zip"
            create_archive(root, destination)
            with zipfile.ZipFile(destination) as archive:
                names = sorted(archive.namelist())
            self.assertIn("multi-agent-graphify-kit/README.md", names)
            self.assertIn("multi-agent-graphify-kit/skills/cogem/SKILL.md", names)
            self.assertIn("multi-agent-graphify-kit/skills/cogem/manifest.txt", names)
            self.assertIn("multi-agent-graphify-kit/skills/cogem/agents/openai.yaml", names)
            self.assertIn("multi-agent-graphify-kit/skills/cogem/schemas/scope-snapshot.schema.json", names)
            self.assertIn("multi-agent-graphify-kit/src/cogem/scope.py", names)
            self.assertIn("multi-agent-graphify-kit/src/cogem/skill_init.py", names)
            self.assertFalse(any("__pycache__" in name for name in names))
            self.assertFalse(any(name.startswith("multi-agent-graphify-kit/.graph/") for name in names))
            self.assertFalse(any(name.endswith(".zip") for name in names))

    def test_archive_rejects_unlisted_skill_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "kit"
            skill = root / "skills" / "demo"
            skill.mkdir(parents=True)
            (root / "README.md").write_text("# Kit\n", encoding="utf-8")
            (skill / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Use when demo behavior is needed.\n---\n",
                encoding="utf-8",
            )
            (skill / "manifest.txt").write_text("SKILL.md\nmanifest.txt\n", encoding="utf-8")
            (skill / "unlisted.md").write_text("not declared\n", encoding="utf-8")
            with self.assertRaises(ManifestError):
                create_archive(root, Path(tmp) / "kit.zip")

    def test_archive_rejects_live_coordination_or_scope_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "multi-agent-graphify-kit"
            skill = root / "skills" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Use when demo behavior is needed.\n---\n",
                encoding="utf-8",
            )
            (skill / "manifest.txt").write_text("SKILL.md\nmanifest.txt\n", encoding="utf-8")
            task_dir = root / ".agents" / "tasks"
            task_dir.mkdir(parents=True)
            (task_dir / "TASK-001.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ManifestError, "live coordination"):
                create_archive(root, Path(tmp) / "kit.zip")

    def test_package_script_runs_directly_when_pythonpath_already_contains_src(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "release"
            root.mkdir()
            (root / "README.md").write_text("# Portable fixture\n", encoding="utf-8")
            output = Path(tmp) / "fixture.zip"
            env = os.environ.copy()
            env["PYTHONPATH"] = str(source / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    str(source / "scripts" / "package_kit.py"),
                    "--root",
                    str(root),
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
                env=env,
                timeout=20,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(output.is_file())

    def test_archive_rejects_missing_manifest_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "kit"
            skill = root / "skills" / "demo"
            skill.mkdir(parents=True)
            (root / "README.md").write_text("# Kit\n", encoding="utf-8")
            (skill / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Use when demo behavior is needed.\n---\n",
                encoding="utf-8",
            )
            (skill / "manifest.txt").write_text("SKILL.md\nmanifest.txt\nreferences/missing.md\n", encoding="utf-8")
            with self.assertRaises(ManifestError):
                create_archive(root, Path(tmp) / "kit.zip")


if __name__ == "__main__":
    unittest.main()
