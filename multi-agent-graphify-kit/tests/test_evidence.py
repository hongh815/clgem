import json
import tempfile
import unittest
from pathlib import Path

from cogem.evidence import review_tree_hash
from cogem.graph import build_project_graph
from cogem.state import CogemState


class EvidenceHashTests(unittest.TestCase):
    def test_review_hash_ignores_coordination_and_generated_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Source\n", encoding="utf-8")
            baseline = review_tree_hash(root)
            (root / ".agents" / "reports").mkdir(parents=True)
            (root / ".agents" / "reports" / "REPORT-001.json").write_text("{}\n", encoding="utf-8")
            (root / ".graph").mkdir()
            (root / ".graph" / "project-graph.json").write_text("{}\n", encoding="utf-8")
            (root / "Comm.md").write_text("generated\n", encoding="utf-8")
            self.assertEqual(review_tree_hash(root), baseline)

    def test_review_hash_changes_with_reviewable_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "README.md"
            path.write_text("# One\n", encoding="utf-8")
            first = review_tree_hash(root)
            path.write_text("# Two\n", encoding="utf-8")
            self.assertNotEqual(review_tree_hash(root), first)

    def test_graph_fingerprint_ignores_messages_reports_and_comm(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Source\n", encoding="utf-8")
            first = build_project_graph(root, CogemState.empty(), {})["input_fingerprint"]
            (root / ".agents" / "messages").mkdir(parents=True)
            (root / ".agents" / "reports").mkdir(parents=True)
            (root / ".agents" / "snapshots").mkdir(parents=True)
            (root / ".agents" / "messages" / "MSG-001.json").write_text(json.dumps({"note": "x"}), encoding="utf-8")
            (root / ".agents" / "reports" / "REPORT-001.json").write_text(json.dumps({"note": "y"}), encoding="utf-8")
            (root / ".agents" / "snapshots" / "TASK-001.json").write_text(json.dumps({"baseline": {}}), encoding="utf-8")
            (root / "Comm.md").write_text("generated\n", encoding="utf-8")
            second = build_project_graph(root, CogemState.empty(), {})["input_fingerprint"]
            self.assertEqual(second, first)

    def test_graph_fingerprint_changes_with_task_or_source_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Source\n", encoding="utf-8")
            first = build_project_graph(root, CogemState.empty(), {})["input_fingerprint"]
            (root / ".agents" / "tasks").mkdir(parents=True)
            (root / ".agents" / "tasks" / "TASK-001.json").write_text(json.dumps({"task": "one"}), encoding="utf-8")
            second = build_project_graph(root, CogemState.empty(), {})["input_fingerprint"]
            self.assertNotEqual(second, first)
            (root / "README.md").write_text("# Changed\n", encoding="utf-8")
            third = build_project_graph(root, CogemState.empty(), {})["input_fingerprint"]
            self.assertNotEqual(third, second)


if __name__ == "__main__":
    unittest.main()
