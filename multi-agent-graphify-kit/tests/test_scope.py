import json
import tempfile
import unittest
from pathlib import Path

from cogem.contracts import TaskRecord
from cogem.scope import ScopeError, check_scope, record_dispatch_snapshot


class ScopeCheckTests(unittest.TestCase):
    def _root(self, root: Path) -> None:
        for name in ("goals", "tasks", "messages", "decisions", "handoffs", "reports", "snapshots"):
            (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
        (root / "README.md").write_text("# Project\n", encoding="utf-8")

    def _task(
        self,
        *,
        write_set=None,
        review_level: str = "standard",
        lease: str = "lease-001",
    ) -> TaskRecord:
        return TaskRecord.from_dict({
            "task_id": "TASK-001",
            "title": "Scoped change",
            "owner": "worker-a",
            "status": "assigned",
            "read_set": ["README.md"],
            "write_set": write_set or ["output.md"],
            "impact_set": [],
            "core_impact_set": [],
            "depends_on": [],
            "acceptance_checks": ["python scripts/cogem.py scope-check TASK-001 --root ."],
            "writing_lease": lease,
            "source_write": True,
            "review_level": review_level,
        })

    def test_modified_in_scope_file_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            (root / "output.md").write_text("before\n", encoding="utf-8")
            task = self._task()
            record_dispatch_snapshot(root, task, "sha256:" + "a" * 64)
            (root / "output.md").write_text("after\n", encoding="utf-8")
            result = check_scope(root, task.task_id, task=task)
            self.assertTrue(result.allowed, result.reasons)
            self.assertEqual([(item.path, item.change_type) for item in result.changes], [("output.md", "modified")])

    def test_creation_deletion_and_rename_are_compared_as_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            docs = root / "docs"
            docs.mkdir()
            (docs / "old.md").write_text("old\n", encoding="utf-8")
            task = self._task(write_set=["docs"])
            record_dispatch_snapshot(root, task, "sha256:" + "b" * 64)
            (docs / "old.md").rename(docs / "new.md")
            result = check_scope(root, task.task_id, task=task)
            self.assertTrue(result.allowed, result.reasons)
            self.assertEqual(
                {(item.path, item.change_type) for item in result.changes},
                {("docs/old.md", "deleted"), ("docs/new.md", "created")},
            )

    def test_out_of_scope_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            (root / "output.md").write_text("before\n", encoding="utf-8")
            task = self._task()
            record_dispatch_snapshot(root, task, "sha256:" + "c" * 64)
            (root / "README.md").write_text("# changed outside scope\n", encoding="utf-8")
            result = check_scope(root, task.task_id, task=task)
            self.assertFalse(result.allowed)
            self.assertIn("OUT_OF_SCOPE_CHANGE", result.reason_codes)
            self.assertEqual(result.out_of_scope_paths, ("README.md",))

    def test_goal_coordination_updates_do_not_contaminate_worker_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            task = self._task()
            record_dispatch_snapshot(root, task, "sha256:" + "9" * 64)
            goal = {
                "goal_id": "GOAL-001",
                "objective": "Deliver the requested outcome.",
                "status": "active",
            }
            (root / ".agents" / "goals" / "GOAL-001.json").write_text(
                json.dumps(goal),
                encoding="utf-8",
            )
            result = check_scope(root, task.task_id, task=task)
            self.assertTrue(result.allowed, result.reasons)
            self.assertEqual(result.changes, ())

    def test_skill_content_and_manifest_changed_in_high_risk_task_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            skill = root / "skills" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("before\n", encoding="utf-8")
            (skill / "manifest.txt").write_text("SKILL.md\nmanifest.txt\n", encoding="utf-8")
            task = self._task(write_set=["skills/demo"], review_level="high-risk")
            record_dispatch_snapshot(root, task, "sha256:" + "d" * 64)
            (skill / "SKILL.md").write_text("after\n", encoding="utf-8")
            (skill / "manifest.txt").write_text("SKILL.md\nmanifest.txt\n# checked\n", encoding="utf-8")
            result = check_scope(root, task.task_id, task=task)
            self.assertTrue(result.allowed, result.reasons)

    def test_skill_content_change_requires_manifest_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            skill = root / "skills" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("before\n", encoding="utf-8")
            (skill / "manifest.txt").write_text("SKILL.md\nmanifest.txt\n", encoding="utf-8")
            task = self._task(write_set=["skills/demo"], review_level="high-risk")
            record_dispatch_snapshot(root, task, "sha256:" + "e" * 64)
            (skill / "SKILL.md").write_text("after\n", encoding="utf-8")
            result = check_scope(root, task.task_id, task=task)
            self.assertFalse(result.allowed)
            self.assertIn("SKILL_MANIFEST_UPDATE_REQUIRED", result.reason_codes)
            self.assertEqual(result.missing_manifests, ("skills/demo/manifest.txt",))

    def test_skill_scope_check_rejects_standard_review_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            task = self._task(write_set=[r"skills\demo\SKILL.md"], review_level="standard")
            record_dispatch_snapshot(root, task, "sha256:" + "f" * 64)
            result = check_scope(root, task.task_id, task=task)
            self.assertFalse(result.allowed)
            self.assertIn("SKILL_REVIEW_LEVEL_REQUIRED", result.reason_codes)

    def test_existing_snapshot_cannot_be_rebased_by_changing_lease_or_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            task = self._task()
            record_dispatch_snapshot(root, task, "sha256:" + "1" * 64)
            changed = self._task(write_set=["README.md"], lease="lease-002")
            with self.assertRaisesRegex(ScopeError, "does not match"):
                record_dispatch_snapshot(root, changed, "sha256:" + "1" * 64)

    def test_malformed_persisted_result_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            task = self._task()
            snapshot_path = record_dispatch_snapshot(root, task, "sha256:" + "2" * 64)
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            snapshot["last_result"] = {
                "task_id": "TASK-999",
                "allowed": True,
                "reason_codes": [],
                "reasons": [],
                "changes": [],
                "out_of_scope_paths": [],
                "missing_manifests": [],
                "checked_tree_hash": "sha256:" + "3" * 64,
            }
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
            with self.assertRaisesRegex(ScopeError, "last_result.task_id"):
                check_scope(root, task.task_id, task=task)


if __name__ == "__main__":
    unittest.main()
