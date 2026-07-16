import json
import tempfile
import unittest
from pathlib import Path

from cogem.evidence import review_tree_hash
from cogem.goal import assess_goal


class GoalLoopTests(unittest.TestCase):
    def _root(self, root: Path) -> None:
        for name in ("goals", "tasks", "messages", "decisions", "handoffs", "reports", "snapshots"):
            (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
        (root / "README.md").write_text("# Project\n", encoding="utf-8")

    def _goal(
        self,
        root: Path,
        *,
        status: str = "active",
        task_ids=None,
        criterion_status: str = "pending",
        evidence=None,
        current_gaps=None,
        tree_hash=None,
        blocker=None,
    ) -> dict:
        payload = {
            "goal_id": "GOAL-001",
            "objective": "Deliver the requested project outcome.",
            "status": status,
            "iteration": 1,
            "criteria": [
                {
                    "criterion_id": "CRIT-001",
                    "description": "The requested behavior is verified.",
                    "status": criterion_status,
                    "evidence": evidence or [],
                }
            ],
            "task_ids": task_ids or [],
            "current_gaps": current_gaps or [],
            "review_tree_hash": tree_hash,
            "blocker": blocker,
            "created_at": "2026-07-16T16:00:00+09:00",
            "updated_at": "2026-07-16T16:00:00+09:00",
        }
        (root / ".agents" / "goals" / "GOAL-001.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )
        return payload

    def _task(
        self,
        root: Path,
        *,
        status: str = "in_progress",
        review_level: str = "standard",
        tree_hash: str | None = None,
    ) -> None:
        payload = {
            "task_id": "TASK-001",
            "title": "Implement the goal",
            "owner": "worker-a",
            "status": status,
            "read_set": ["README.md"],
            "write_set": ["output.md"],
            "impact_set": [],
            "core_impact_set": [],
            "depends_on": [],
            "acceptance_checks": ["tests"],
            "writing_lease": "lease-goal-task",
            "source_write": True,
            "priority": "normal",
            "review_level": review_level,
            "review_tree_hash": tree_hash,
        }
        (root / ".agents" / "tasks" / "TASK-001.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def _scope_evidence(self, root: Path, tree_hash: str, *, review_level: str = "standard") -> None:
        payload = {
            "version": 1,
            "task_id": "TASK-001",
            "writing_lease": "lease-goal-task",
            "write_set": ["output.md"],
            "review_level": review_level,
            "graph_fingerprint": f"sha256:{'0' * 64}",
            "baseline": {},
            "last_result": {
                "task_id": "TASK-001",
                "allowed": True,
                "reason_codes": [],
                "reasons": [],
                "changes": [],
                "out_of_scope_paths": [],
                "missing_manifests": [],
                "checked_tree_hash": tree_hash,
            },
        }
        (root / ".agents" / "snapshots" / "TASK-001.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def _task_review(self, root: Path, tree_hash: str, *, kind: str = "independent-review") -> None:
        adversarial = kind == "adversarial-review"
        payload = {
            "report_id": "REPORT-002" if adversarial else "REPORT-001",
            "agent_id": "independent-reviewer",
            "task_id": "TASK-001",
            "goal_id": None,
            "kind": kind,
            "status": "pass",
            "summary": "The task satisfies its contract.",
            "evidence": ["task review complete"],
            "created_at": "2026-07-16T16:30:00+09:00",
            "review_proof": {
                "engine": "antigravity-preview-05-2026",
                "session_id": f"{kind}-session",
                "fresh_context": True,
                "permissions": "read-only",
                "source_write_performed": False,
                "reviewed_tree_hash": tree_hash,
                "prior_findings_provided": False,
                "prompt_mode": "adversarial" if adversarial else "independent",
                "pass_index": 2 if adversarial else 1,
            },
        }
        (root / ".agents" / "reports" / f"{payload['report_id']}.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def _completed_task(self, root: Path, *, review_level: str = "standard", adversarial: bool = False) -> str:
        tree_hash = review_tree_hash(root)
        self._task(root, status="closed", review_level=review_level, tree_hash=tree_hash)
        self._scope_evidence(root, tree_hash, review_level=review_level)
        self._task_review(root, tree_hash)
        if adversarial:
            self._task_review(root, tree_hash, kind="adversarial-review")
        return tree_hash

    def _goal_review(self, root: Path, tree_hash: str, *, status: str = "pass") -> None:
        payload = {
            "report_id": "REPORT-003",
            "agent_id": "independent-reviewer",
            "task_id": None,
            "goal_id": "GOAL-001",
            "kind": "goal-review",
            "status": status,
            "summary": "The integrated outcome satisfies the goal.",
            "evidence": ["goal criteria checked"],
            "created_at": "2026-07-16T17:00:00+09:00",
            "review_proof": {
                "engine": "antigravity-preview-05-2026",
                "session_id": "goal-review-session",
                "fresh_context": True,
                "permissions": "read-only",
                "source_write_performed": False,
                "reviewed_tree_hash": tree_hash,
                "prior_findings_provided": False,
                "prompt_mode": "independent",
                "pass_index": 1,
            },
        }
        (root / ".agents" / "reports" / "REPORT-003.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def test_goal_without_tasks_requires_decomposition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            self._goal(root)
            result = assess_goal(root, "GOAL-001")
            self.assertEqual(result.next_action, "decompose")

    def test_open_task_requires_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            self._task(root)
            self._goal(root, task_ids=["TASK-001"])
            result = assess_goal(root, "GOAL-001")
            self.assertEqual(result.next_action, "execute")
            self.assertEqual(result.open_task_ids, ("TASK-001",))

    def test_failed_criterion_or_recorded_gap_requires_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            self._completed_task(root)
            self._goal(
                root,
                task_ids=["TASK-001"],
                criterion_status="fail",
                current_gaps=["The CLI still lacks the requested behavior."],
            )
            result = assess_goal(root, "GOAL-001")
            self.assertEqual(result.next_action, "repair")
            self.assertEqual(result.failed_criteria, ("CRIT-001",))

    def test_completed_tasks_need_criterion_evidence_before_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            self._completed_task(root)
            self._goal(root, task_ids=["TASK-001"])
            result = assess_goal(root, "GOAL-001")
            self.assertEqual(result.next_action, "verify")
            self.assertEqual(result.pending_criteria, ("CRIT-001",))

    def test_verified_goal_requires_fresh_goal_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            digest = self._completed_task(root)
            self._goal(
                root,
                status="verifying",
                task_ids=["TASK-001"],
                criterion_status="pass",
                evidence=["python tests passed"],
                tree_hash=digest,
            )
            result = assess_goal(root, "GOAL-001")
            self.assertEqual(result.next_action, "review")

    def test_matching_goal_review_makes_goal_ready_to_close(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            digest = self._completed_task(root)
            self._goal(
                root,
                status="verifying",
                task_ids=["TASK-001"],
                criterion_status="pass",
                evidence=["python tests passed"],
                tree_hash=digest,
            )
            self._goal_review(root, digest)
            result = assess_goal(root, "GOAL-001")
            self.assertEqual(result.next_action, "ready_to_close")

    def test_achieved_goal_with_matching_review_is_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            digest = self._completed_task(root)
            self._goal(
                root,
                status="achieved",
                task_ids=["TASK-001"],
                criterion_status="pass",
                evidence=["python tests passed"],
                tree_hash=digest,
            )
            self._goal_review(root, digest)
            result = assess_goal(root, "GOAL-001")
            self.assertEqual(result.next_action, "complete")

    def test_closed_task_without_required_review_evidence_blocks_goal_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            digest = review_tree_hash(root)
            self._task(root, status="closed", tree_hash=digest)
            self._scope_evidence(root, digest)
            self._goal(
                root,
                status="verifying",
                task_ids=["TASK-001"],
                criterion_status="pass",
                evidence=["python tests passed"],
                tree_hash=digest,
            )
            self._goal_review(root, digest)
            result = assess_goal(root, "GOAL-001")
            self.assertEqual(result.next_action, "review")
            self.assertIn("TASK-001", result.task_evidence_issues[0])

    def test_high_risk_task_requires_adversarial_review_before_goal_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            digest = self._completed_task(root, review_level="high-risk")
            self._goal(
                root,
                status="verifying",
                task_ids=["TASK-001"],
                criterion_status="pass",
                evidence=["python tests passed"],
                tree_hash=digest,
            )
            self._goal_review(root, digest)
            result = assess_goal(root, "GOAL-001")
            self.assertEqual(result.next_action, "review")
            self.assertTrue(any("adversarial" in issue for issue in result.task_evidence_issues))

    def test_failed_current_goal_review_requires_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            digest = self._completed_task(root)
            self._goal(
                root,
                status="verifying",
                task_ids=["TASK-001"],
                criterion_status="pass",
                evidence=["python tests passed"],
                tree_hash=digest,
            )
            self._goal_review(root, digest, status="fail")
            result = assess_goal(root, "GOAL-001")
            self.assertEqual(result.next_action, "repair")

    def test_blocked_goal_reports_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            self._goal(
                root,
                status="blocked",
                blocker="External production credentials are unavailable.",
            )
            result = assess_goal(root, "GOAL-001")
            self.assertEqual(result.next_action, "blocked")


if __name__ == "__main__":
    unittest.main()
