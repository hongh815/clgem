import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def run_cli(self, root, *args, env=None):
        script = Path(__file__).resolve().parents[1] / "scripts" / "cogem.py"
        command_env = os.environ.copy()
        command_env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
        if env:
            command_env.update(env)
        return subprocess.run(
            [sys.executable, str(script), *args, "--root", str(root)],
            text=True,
            capture_output=True,
            env=command_env,
            timeout=10,
        )

    def test_graph_command_is_non_interactive_and_creates_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("tasks", "messages", "decisions", "handoffs", "reports"):
                (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
            (root / "README.md").write_text("# Project\n", encoding="utf-8")
            result = self.run_cli(root, "graph")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("input(", result.stdout + result.stderr)
            self.assertTrue((root / ".graph" / "project-graph.json").exists())

    def test_parallel_command_returns_unsafe_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_dir = root / ".agents" / "tasks"
            for name in ("tasks", "messages", "decisions", "handoffs", "reports"):
                (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
            base = {
                "title": "x", "status": "ready", "read_set": [], "impact_set": [],
                "core_impact_set": [], "depends_on": [], "acceptance_checks": [], "review_level": "standard",
            }
            (task_dir / "a.json").write_text(json.dumps({
                **base, "task_id": "TASK-001", "owner": "a", "write_set": ["same.md"], "writing_lease": "lease-a",
            }), encoding="utf-8")
            (task_dir / "b.json").write_text(json.dumps({
                **base, "task_id": "TASK-002", "owner": "b", "write_set": ["same.md"], "writing_lease": "lease-b",
            }), encoding="utf-8")
            result = self.run_cli(root, "parallel", "TASK-001", "TASK-002")
            self.assertEqual(result.returncode, 5)
            self.assertIn("WRITE_WRITE_CONFLICT", result.stdout)

    def test_engine_plan_resolves_five_roles_with_antigravity_review(self):
        root = Path(__file__).resolve().parents[1]
        result = self.run_cli(
            root,
            "engine-plan",
            "--require-resolved",
            "--show-engine-ids",
            env={
                "COGEM_COORDINATOR_ENGINE": "gpt-5.6-sol",
                "COGEM_BALANCED_ENGINE": "gpt-5.6-terra",
                "COGEM_REVIEW_ENGINE": "antigravity-preview-05-2026",
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = json.loads(result.stdout)
        self.assertEqual(len(rows), 5)
        by_role = {row["role"]: row for row in rows}
        reviewer = by_role["independent-reviewer"]
        self.assertEqual(reviewer["engine_id"], "antigravity-preview-05-2026")
        self.assertEqual(reviewer["review_passes"], ["adversarial", "independent"])

    def test_model_plan_remains_a_compatibility_alias(self):
        root = Path(__file__).resolve().parents[1]
        result = self.run_cli(root, "model-plan")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)), 5)


if __name__ == "__main__":
    unittest.main()


class GovernanceCliTests(CliTests):
    def _assigned_project(self, root: Path) -> None:
        import shutil
        for name in ("tasks", "messages", "decisions", "handoffs", "reports"):
            (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(__file__).resolve().parents[1] / "agent-models.json", root / "agent-models.json")
        (root / "README.md").write_text("# Project\n", encoding="utf-8")
        task = {
            "task_id": "TASK-030", "title": "Dispatch", "owner": "worker-a", "status": "assigned",
            "read_set": ["README.md"], "write_set": ["out.md"], "impact_set": [], "core_impact_set": [],
            "depends_on": [], "acceptance_checks": ["tests"], "writing_lease": "lease-30",
            "source_write": True, "review_level": "standard"
        }
        (root / ".agents" / "tasks" / "TASK-030.json").write_text(json.dumps(task), encoding="utf-8")

    def test_dispatch_check_uses_dedicated_blocked_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._assigned_project(root)
            result = self.run_cli(root, "dispatch-check", "TASK-030")
            self.assertEqual(result.returncode, 6)
            self.assertIn("GRAPH_NOT_GENERATED", result.stdout)

    def test_dispatch_records_snapshot_and_scope_check_uses_exit_code_seven(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._assigned_project(root)
            graph = self.run_cli(root, "graph")
            self.assertEqual(graph.returncode, 0, graph.stderr)
            dispatch = self.run_cli(root, "dispatch-check", "TASK-030")
            self.assertEqual(dispatch.returncode, 0, dispatch.stderr + dispatch.stdout)
            self.assertTrue((root / ".agents" / "snapshots" / "TASK-030.json").is_file())
            (root / "README.md").write_text("# Outside scope\n", encoding="utf-8")
            scope = self.run_cli(root, "scope-check", "TASK-030")
            self.assertEqual(scope.returncode, 7, scope.stderr + scope.stdout)
            self.assertIn("OUT_OF_SCOPE_CHANGE", scope.stdout)

    def test_review_hash_is_non_interactive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Project\n", encoding="utf-8")
            result = self.run_cli(root, "review-hash")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertRegex(result.stdout.strip(), r"^sha256:[0-9a-f]{64}$")

    def test_skill_init_creates_a_valid_codex_compatible_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_cli(root, "skill-init", "example-skill", "--resources", "references,assets,schemes")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["skill"], "skills/example-skill")
            self.assertTrue((root / "skills" / "example-skill" / "agents" / "openai.yaml").is_file())
            self.assertTrue((root / "skills" / "example-skill" / "schemas").is_dir())

    def test_skill_check_json_is_machine_readable(self):
        root = Path(__file__).resolve().parents[1]
        result = self.run_cli(root, "skill-check", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [])

    def test_goal_init_records_user_objective_and_goal_check_requests_decomposition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_cli(
                root,
                "goal-init",
                "GOAL-001",
                "--objective",
                "Build a persistent leader-driven engineering loop.",
                "--criterion",
                "The leader continues until the goal passes review.",
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            goal_path = root / ".agents" / "goals" / "GOAL-001.json"
            self.assertTrue(goal_path.is_file())
            payload = json.loads(goal_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "active")
            self.assertEqual(payload["criteria"][0]["status"], "pending")

            status = self.run_cli(root, "goal-check", "GOAL-001")
            self.assertEqual(status.returncode, 0, status.stderr + status.stdout)
            self.assertEqual(json.loads(status.stdout)["next_action"], "decompose")
