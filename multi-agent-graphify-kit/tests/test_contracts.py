import json
import tempfile
import unittest
from pathlib import Path

from cogem.contracts import ContractError, GoalRecord, ReportRecord, TaskRecord
from cogem.state import load_state


class ContractTests(unittest.TestCase):
    def test_goal_parses_objective_criteria_and_iteration(self):
        goal = GoalRecord.from_dict({
            "goal_id": "GOAL-001",
            "objective": "Deliver the user-requested outcome.",
            "status": "active",
            "iteration": 2,
            "criteria": [{
                "criterion_id": "CRIT-001",
                "description": "The requested behavior works.",
                "status": "pending",
                "evidence": [],
            }],
            "task_ids": ["TASK-001"],
            "current_gaps": [],
            "review_tree_hash": None,
            "blocker": None,
            "created_at": "2026-07-16T16:00:00+09:00",
            "updated_at": "2026-07-16T16:30:00+09:00",
        })
        self.assertEqual(goal.goal_id, "GOAL-001")
        self.assertEqual(goal.iteration, 2)
        self.assertEqual(goal.criteria[0].criterion_id, "CRIT-001")

    def test_task_parses_complete_contract(self):
        task = TaskRecord.from_dict({
            "task_id": "TASK-001",
            "title": "Define shared protocol",
            "owner": "worker-a",
            "status": "ready",
            "read_set": ["docs/architecture.md"],
            "write_set": ["skills/cogem/SKILL.md"],
            "impact_set": ["docs/agent-roles.md"],
            "core_impact_set": [],
            "depends_on": [],
            "acceptance_checks": ["python -m unittest tests.test_contracts -v"],
            "writing_lease": "lease-worker-a",
            "review_level": "high-risk"
        })
        self.assertEqual(task.task_id, "TASK-001")
        self.assertEqual(task.status, "ready")
        self.assertEqual(task.write_set, ("skills/cogem/SKILL.md",))

    def test_task_requires_review_level(self):
        with self.assertRaisesRegex(ContractError, "review_level"):
            TaskRecord.from_dict({
                "task_id": "TASK-099", "title": "Missing review level", "owner": "worker-a",
                "status": "ready", "read_set": [], "write_set": ["docs/a.md"],
                "impact_set": [], "core_impact_set": [], "depends_on": [],
                "acceptance_checks": [], "writing_lease": "lease-99"
            })

    def test_task_rejects_unknown_status(self):
        with self.assertRaisesRegex(ContractError, "status"):
            TaskRecord.from_dict({
                "task_id": "TASK-001", "title": "x", "owner": "worker-a",
                "status": "almost-done", "read_set": [], "write_set": [],
                "impact_set": [], "core_impact_set": [], "depends_on": [],
                "acceptance_checks": [], "writing_lease": "lease-a", "review_level": "standard"
            })

    def test_state_loader_rejects_duplicate_task_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_dir = root / ".agents" / "tasks"
            task_dir.mkdir(parents=True)
            payload = {
                "task_id": "TASK-001", "title": "x", "owner": "worker-a",
                "status": "ready", "read_set": [], "write_set": ["a.md"],
                "impact_set": [], "core_impact_set": [], "depends_on": [],
                "acceptance_checks": [], "writing_lease": "lease-a", "review_level": "standard"
            }
            (task_dir / "one.json").write_text(json.dumps(payload), encoding="utf-8")
            (task_dir / "two.json").write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "duplicate task_id"):
                load_state(root)


if __name__ == "__main__":
    unittest.main()


class ReviewContractTests(unittest.TestCase):
    def test_goal_review_requires_goal_id_and_independent_proof(self):
        report = ReportRecord.from_dict({
            "report_id": "REPORT-050",
            "agent_id": "independent-reviewer",
            "task_id": None,
            "goal_id": "GOAL-001",
            "kind": "goal-review",
            "status": "pass",
            "summary": "Goal passed.",
            "evidence": ["criteria"],
            "created_at": "2026-07-16T17:00:00+09:00",
            "review_proof": {
                "engine": "antigravity-preview-05-2026",
                "session_id": "goal-review",
                "fresh_context": True,
                "permissions": "read-only",
                "source_write_performed": False,
                "reviewed_tree_hash": "sha256:" + "a" * 64,
                "prior_findings_provided": False,
                "prompt_mode": "independent",
                "pass_index": 1,
            },
        })
        self.assertEqual(report.goal_id, "GOAL-001")

    def test_goal_review_rejects_prior_findings_context(self):
        with self.assertRaisesRegex(ContractError, "prior findings"):
            ReportRecord.from_dict({
                "report_id": "REPORT-051",
                "agent_id": "independent-reviewer",
                "task_id": None,
                "goal_id": "GOAL-001",
                "kind": "goal-review",
                "status": "pass",
                "summary": "Goal passed.",
                "evidence": ["criteria"],
                "created_at": "2026-07-16T17:00:00+09:00",
                "review_proof": {
                    "engine": "antigravity-preview-05-2026",
                    "session_id": "goal-review-with-history",
                    "fresh_context": True,
                    "permissions": "read-only",
                    "source_write_performed": False,
                    "reviewed_tree_hash": "sha256:" + "a" * 64,
                    "prior_findings_provided": True,
                    "prompt_mode": "independent",
                    "pass_index": 1,
                },
            })

    def test_task_accepts_explicit_high_risk_review_level(self):
        task = TaskRecord.from_dict({
            "task_id": "TASK-010", "title": "Change orchestration", "owner": "worker-a",
            "status": "ready", "read_set": [], "write_set": ["AGENTS.md"],
            "impact_set": [], "core_impact_set": ["AGENTS.md"], "depends_on": [],
            "acceptance_checks": [], "writing_lease": "lease-10", "review_level": "high-risk"
        })
        self.assertEqual(task.review_level, "high-risk")

    def test_task_accepts_review_tree_hash(self):
        task = TaskRecord.from_dict({
            "task_id": "TASK-011", "title": "Bind review", "owner": "worker-a",
            "status": "review_ready", "read_set": [], "write_set": ["x.md"],
            "impact_set": [], "core_impact_set": [], "depends_on": [],
            "acceptance_checks": [], "writing_lease": "lease-11",
            "review_level": "standard",
            "review_tree_hash": "sha256:" + "b" * 64
        })
        self.assertEqual(task.review_tree_hash, "sha256:" + "b" * 64)

    def test_review_report_rejects_non_fresh_context(self):
        from cogem.contracts import ReportRecord
        with self.assertRaisesRegex(ContractError, "fresh_context"):
            ReportRecord.from_dict({
                "report_id": "REPORT-010", "agent_id": "independent-reviewer", "task_id": "TASK-010",
                "kind": "independent-review", "status": "pass", "summary": "Reviewed", "evidence": ["tests"],
                "created_at": "2026-07-16T12:00:00+09:00",
                "review_proof": {
                    "engine": "antigravity-preview-05-2026", "session_id": "session-1",
                    "fresh_context": False, "permissions": "read-only", "source_write_performed": False,
                    "reviewed_tree_hash": "sha256:" + "a" * 64, "prior_findings_provided": False,
                    "prompt_mode": "independent", "pass_index": 1
                }
            })
