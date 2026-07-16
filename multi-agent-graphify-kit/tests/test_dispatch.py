import json
import shutil
import tempfile
import unittest
from pathlib import Path

from cogem.config import load_config
from cogem.dispatch import check_dispatch
from cogem.graph import build_project_graph, write_graph_artifacts
from cogem.state import load_state


class DispatchTests(unittest.TestCase):
    def _project(
        self,
        root: Path,
        *,
        status: str = "assigned",
        depends_on=None,
        write_set=None,
        review_level: str = "standard",
    ) -> None:
        for name in ("tasks", "messages", "decisions", "handoffs", "reports"):
            (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
        source_policy = Path(__file__).resolve().parents[1] / "agent-models.json"
        shutil.copy2(source_policy, root / "agent-models.json")
        (root / "README.md").write_text("# Project\n", encoding="utf-8")
        task = {
            "task_id": "TASK-001",
            "title": "Write output",
            "owner": "worker-a",
            "status": status,
            "read_set": ["README.md"],
            "write_set": write_set or ["output.md"],
            "impact_set": [],
            "core_impact_set": [],
            "depends_on": depends_on or [],
            "acceptance_checks": ["python scripts/cogem.py validate --root ."],
            "writing_lease": "lease-task-001",
            "source_write": True,
            "review_level": review_level,
        }
        (root / ".agents" / "tasks" / "TASK-001.json").write_text(json.dumps(task), encoding="utf-8")

    def _graph(self, root: Path) -> None:
        config = load_config(root)
        state = load_state(root, config["state_dir"])
        graph = build_project_graph(root, state, config)
        write_graph_artifacts(graph, root / config["graph_dir"])

    def test_assigned_task_with_fresh_graph_is_dispatchable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root)
            self._graph(root)
            result = check_dispatch(root, "TASK-001")
            self.assertTrue(result.allowed, result.reasons)

    def test_allowed_dispatch_can_record_an_immutable_scope_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root)
            self._graph(root)
            result = check_dispatch(root, "TASK-001", record_snapshot=True)
            self.assertTrue(result.allowed, result.reasons)
            snapshot = root / ".agents" / "snapshots" / "TASK-001.json"
            self.assertTrue(snapshot.is_file())
            payload = json.loads(snapshot.read_text(encoding="utf-8"))
            self.assertEqual(payload["task_id"], "TASK-001")
            self.assertEqual(payload["write_set"], ["output.md"])

    def test_ready_task_is_not_dispatchable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, status="ready")
            self._graph(root)
            result = check_dispatch(root, "TASK-001")
            self.assertFalse(result.allowed)
            self.assertIn("TASK_NOT_ASSIGNED", result.reason_codes)

    def test_missing_graph_blocks_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root)
            result = check_dispatch(root, "TASK-001")
            self.assertFalse(result.allowed)
            self.assertIn("GRAPH_NOT_GENERATED", result.reason_codes)

    def test_stale_graph_blocks_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root)
            self._graph(root)
            (root / "README.md").write_text("# Changed after graph\n", encoding="utf-8")
            result = check_dispatch(root, "TASK-001")
            self.assertFalse(result.allowed)
            self.assertIn("GRAPH_STALE", result.reason_codes)

    def test_unfinished_dependency_blocks_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, depends_on=["TASK-000"])
            predecessor = {
                "task_id": "TASK-000", "title": "Predecessor", "owner": "worker-b",
                "status": "review_ready", "read_set": [], "write_set": ["pre.md"],
                "impact_set": [], "core_impact_set": [], "depends_on": [],
                "acceptance_checks": [], "writing_lease": "lease-task-000",
                "source_write": True, "review_level": "standard"
            }
            (root / ".agents" / "tasks" / "TASK-000.json").write_text(json.dumps(predecessor), encoding="utf-8")
            self._graph(root)
            result = check_dispatch(root, "TASK-001")
            self.assertFalse(result.allowed)
            self.assertIn("DEPENDENCY_NOT_COMPLETE", result.reason_codes)

    def test_skill_task_with_standard_review_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, write_set=["skills/demo/SKILL.md"], review_level="standard")
            self._graph(root)
            result = check_dispatch(root, "TASK-001")
            self.assertFalse(result.allowed)
            self.assertIn("SKILL_REVIEW_LEVEL_REQUIRED", result.reason_codes)

    def test_skill_task_with_high_risk_review_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, write_set=["skills/demo/SKILL.md"], review_level="high-risk")
            self._graph(root)
            result = check_dispatch(root, "TASK-001")
            self.assertTrue(result.allowed, result.reasons)

    def test_normal_task_with_standard_review_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, write_set=["docs/guide.md"], review_level="standard")
            self._graph(root)
            result = check_dispatch(root, "TASK-001")
            self.assertTrue(result.allowed, result.reasons)

    def test_nested_skill_subfile_is_classified_as_skill_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, write_set=["skills/demo/references/guide.md"], review_level="standard")
            self._graph(root)
            result = check_dispatch(root, "TASK-001")
            self.assertIn("SKILL_REVIEW_LEVEL_REQUIRED", result.reason_codes)

    def test_windows_skill_path_is_classified_as_skill_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._project(root, write_set=[r"skills\demo\SKILL.md"], review_level="standard")
            self._graph(root)
            result = check_dispatch(root, "TASK-001")
            self.assertIn("SKILL_REVIEW_LEVEL_REQUIRED", result.reason_codes)


if __name__ == "__main__":
    unittest.main()
