import json
import tempfile
import unittest
from pathlib import Path

from cogem.contracts import GoalRecord, TaskRecord
from cogem.graph import build_project_graph, graph_to_mermaid, write_graph_artifacts
from cogem.state import CogemState


class GraphTests(unittest.TestCase):
    def test_goal_nodes_connect_to_their_work_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = TaskRecord.from_dict({
                "task_id": "TASK-001", "title": "Implement goal", "owner": "worker-a",
                "status": "ready", "read_set": [], "write_set": ["output.md"],
                "impact_set": [], "core_impact_set": [], "depends_on": [],
                "acceptance_checks": [], "writing_lease": "lease-goal",
                "review_level": "standard",
            })
            goal = GoalRecord.from_dict({
                "goal_id": "GOAL-001",
                "objective": "Deliver the requested outcome.",
                "status": "active",
                "iteration": 1,
                "criteria": [{
                    "criterion_id": "CRIT-001", "description": "It works.",
                    "status": "pending", "evidence": [],
                }],
                "task_ids": ["TASK-001"],
                "current_gaps": [],
                "review_tree_hash": None,
                "blocker": None,
                "created_at": "2026-07-16T16:00:00+09:00",
                "updated_at": "2026-07-16T16:00:00+09:00",
            })
            state = CogemState(
                tasks={"TASK-001": task},
                decisions={},
                handoffs={},
                messages=(),
                reports=(),
                goals={"GOAL-001": goal},
            )
            graph = build_project_graph(root, state, {})
            self.assertIn("goal:GOAL-001", {node["id"] for node in graph["nodes"]})
            self.assertIn(
                {"source": "goal:GOAL-001", "target": "task:TASK-001", "type": "drives"},
                graph["edges"],
            )

    def test_scans_files_and_markdown_links_deterministically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "README.md").write_text("See [architecture](docs/architecture.md).\n", encoding="utf-8")
            (root / "docs" / "architecture.md").write_text("# Architecture\n", encoding="utf-8")
            graph = build_project_graph(root, CogemState.empty(), {"ignore": [".graph/**"]})
            ids = [node["id"] for node in graph["nodes"]]
            self.assertEqual(ids, sorted(ids))
            self.assertIn("file:README.md", ids)
            self.assertIn("file:docs/architecture.md", ids)
            self.assertIn({"source": "file:README.md", "target": "file:docs/architecture.md", "type": "links_to"}, graph["edges"])
            self.assertEqual(graph["broken_links"], [])
            self.assertRegex(graph["input_fingerprint"], r"^sha256:[0-9a-f]{64}$")

    def test_reports_broken_local_markdown_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("[missing](docs/missing.md)\n", encoding="utf-8")
            graph = build_project_graph(root, CogemState.empty(), {})
            self.assertEqual(graph["broken_links"][0]["target"], "docs/missing.md")

    def test_writes_json_mermaid_and_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# x\n", encoding="utf-8")
            graph = build_project_graph(root, CogemState.empty(), {})
            out = root / ".graph"
            write_graph_artifacts(graph, out)
            self.assertTrue((out / "project-graph.json").is_file())
            self.assertTrue((out / "project-graph.mmd").is_file())
            self.assertTrue((out / "project-graph.md").is_file())
            loaded = json.loads((out / "project-graph.json").read_text(encoding="utf-8"))
            self.assertEqual(loaded["version"], 1)
            self.assertIn("flowchart LR", graph_to_mermaid(graph))

    def test_markdown_angle_target_preserves_spaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "file name.md").write_text("# Named\n", encoding="utf-8")
            (root / "README.md").write_text("[named](<docs/file name.md>)\n", encoding="utf-8")
            graph = build_project_graph(root, CogemState.empty(), {})
            self.assertIn(
                {"source": "file:README.md", "target": "file:docs/file name.md", "type": "links_to"},
                graph["edges"],
            )

    def test_scans_generic_json_path_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "architecture.md").write_text("# Architecture\n", encoding="utf-8")
            (root / "settings.json").write_text(json.dumps({"path": "docs/architecture.md"}), encoding="utf-8")
            graph = build_project_graph(root, CogemState.empty(), {})
            self.assertIn(
                {"source": "file:settings.json", "target": "file:docs/architecture.md", "type": "references"},
                graph["edges"],
            )

    def test_reports_invalid_generic_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "broken.json").write_text("{not-json", encoding="utf-8")
            graph = build_project_graph(root, CogemState.empty(), {})
            self.assertEqual(graph["invalid_json"][0]["source"], "broken.json")

    def test_graph_root_is_portable(self):
        roots = []
        graphs = []
        for _ in range(2):
            temporary = tempfile.TemporaryDirectory()
            roots.append(temporary)
            root = Path(temporary.name)
            (root / "README.md").write_text("# Same\n", encoding="utf-8")
            graphs.append(build_project_graph(root, CogemState.empty(), {}))
        self.assertEqual(graphs[0]["root"], ".")
        self.assertEqual(graphs[0], graphs[1])
        for temporary in roots:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
