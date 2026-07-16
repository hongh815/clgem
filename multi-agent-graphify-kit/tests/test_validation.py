import json
import shutil
import tempfile
import unittest
from pathlib import Path

from cogem.validation import validate_project


class ValidationTests(unittest.TestCase):
    def test_goal_referencing_missing_task_is_project_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("goals", "tasks", "messages", "decisions", "handoffs", "reports"):
                (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
            goal = {
                "goal_id": "GOAL-001",
                "objective": "Deliver the requested outcome.",
                "status": "active",
                "iteration": 1,
                "criteria": [{
                    "criterion_id": "CRIT-001", "description": "It works.",
                    "status": "pending", "evidence": [],
                }],
                "task_ids": ["TASK-999"],
                "current_gaps": [],
                "review_tree_hash": None,
                "blocker": None,
                "created_at": "2026-07-16T16:00:00+09:00",
                "updated_at": "2026-07-16T16:00:00+09:00",
            }
            (root / ".agents" / "goals" / "GOAL-001.json").write_text(
                json.dumps(goal),
                encoding="utf-8",
            )
            diagnostics = validate_project(root, model_policy_required=False)
            self.assertIn("MISSING_GOAL_TASK", [d.code for d in diagnostics])

    def test_achieved_goal_requires_complete_goal_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("goals", "tasks", "messages", "decisions", "handoffs", "reports"):
                (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
            goal = {
                "goal_id": "GOAL-001",
                "objective": "Deliver the requested outcome.",
                "status": "achieved",
                "iteration": 1,
                "criteria": [{
                    "criterion_id": "CRIT-001", "description": "It works.",
                    "status": "pending", "evidence": [],
                }],
                "task_ids": [],
                "current_gaps": [],
                "review_tree_hash": None,
                "blocker": None,
                "created_at": "2026-07-16T16:00:00+09:00",
                "updated_at": "2026-07-16T16:00:00+09:00",
            }
            (root / ".agents" / "goals" / "GOAL-001.json").write_text(
                json.dumps(goal),
                encoding="utf-8",
            )
            diagnostics = validate_project(root, model_policy_required=False)
            self.assertIn("GOAL_NOT_COMPLETE", [d.code for d in diagnostics])
    def test_valid_minimal_project_has_no_error_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("tasks", "messages", "decisions", "handoffs", "reports"):
                (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
            (root / "README.md").write_text("# Project\n", encoding="utf-8")
            diagnostics = validate_project(root, model_policy_required=False)
            self.assertFalse([d for d in diagnostics if d.severity == "error"])

    def test_broken_markdown_link_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("tasks", "messages", "decisions", "handoffs", "reports"):
                (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
            (root / "README.md").write_text("[missing](missing.md)\n", encoding="utf-8")
            diagnostics = validate_project(root, model_policy_required=False)
            self.assertIn("BROKEN_LINK", [d.code for d in diagnostics])

    def test_invalid_generic_json_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("tasks", "messages", "decisions", "handoffs", "reports"):
                (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
            (root / "broken.json").write_text("{not-json", encoding="utf-8")
            diagnostics = validate_project(root, model_policy_required=False)
            self.assertIn("INVALID_JSON", [d.code for d in diagnostics])

    def test_skill_task_with_standard_review_is_project_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("tasks", "messages", "decisions", "handoffs", "reports"):
                (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
            task = {
                "task_id": "TASK-002", "title": "Unsafe skill change", "owner": "worker-a",
                "status": "ready", "read_set": [], "write_set": ["skills/demo/SKILL.md"],
                "impact_set": [], "core_impact_set": [], "depends_on": [],
                "acceptance_checks": [], "writing_lease": "lease-skill",
                "source_write": True, "review_level": "standard"
            }
            (root / ".agents" / "tasks" / "TASK-002.json").write_text(json.dumps(task), encoding="utf-8")
            diagnostics = validate_project(root, model_policy_required=False)
            self.assertIn("SKILL_REVIEW_LEVEL_REQUIRED", [d.code for d in diagnostics])

    def test_review_ready_task_requires_passing_scope_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("tasks", "messages", "decisions", "handoffs", "reports", "snapshots"):
                (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
            (root / "README.md").write_text("# Project\n", encoding="utf-8")
            task = {
                "task_id": "TASK-003", "title": "Ready for review", "owner": "worker-a",
                "status": "review_ready", "read_set": [], "write_set": ["README.md"],
                "impact_set": [], "core_impact_set": [], "depends_on": [],
                "acceptance_checks": [], "writing_lease": "lease-review-ready",
                "source_write": True, "review_level": "standard"
            }
            (root / ".agents" / "tasks" / "TASK-003.json").write_text(json.dumps(task), encoding="utf-8")
            diagnostics = validate_project(root, model_policy_required=False)
            self.assertIn("SCOPE_CHECK_REQUIRED", [d.code for d in diagnostics])

    def test_handoff_requires_passing_scope_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("tasks", "messages", "decisions", "handoffs", "reports", "snapshots"):
                (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
            (root / "README.md").write_text("# Project\n", encoding="utf-8")
            task = {
                "task_id": "TASK-004", "title": "Handoff", "owner": "worker-a",
                "status": "in_progress", "read_set": [], "write_set": ["README.md"],
                "impact_set": [], "core_impact_set": [], "depends_on": [],
                "acceptance_checks": [], "writing_lease": "lease-handoff",
                "source_write": True, "review_level": "standard"
            }
            handoff = {
                "handoff_id": "HANDOFF-004", "task_id": "TASK-004",
                "from_agent": "worker-a", "to_agent": "coordinator",
                "status": "pending", "summary": "Ready", "artifacts": ["README.md"],
                "created_at": "2026-07-16T12:00:00+09:00"
            }
            (root / ".agents" / "tasks" / "TASK-004.json").write_text(json.dumps(task), encoding="utf-8")
            (root / ".agents" / "handoffs" / "HANDOFF-004.json").write_text(json.dumps(handoff), encoding="utf-8")
            diagnostics = validate_project(root, model_policy_required=False)
            self.assertIn("SCOPE_CHECK_REQUIRED", [d.code for d in diagnostics])

    def test_review_ready_task_rejects_failing_persisted_scope_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("tasks", "messages", "decisions", "handoffs", "reports", "snapshots"):
                (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
            (root / "README.md").write_text("# Project\n", encoding="utf-8")
            task = {
                "task_id": "TASK-005", "title": "Failing scope", "owner": "worker-a",
                "status": "review_ready", "read_set": [], "write_set": ["README.md"],
                "impact_set": [], "core_impact_set": [], "depends_on": [],
                "acceptance_checks": [], "writing_lease": "lease-failing-scope",
                "source_write": True, "review_level": "standard"
            }
            snapshot = {
                "version": 1, "task_id": "TASK-005", "writing_lease": "lease-failing-scope",
                "write_set": ["README.md"], "review_level": "standard",
                "graph_fingerprint": "sha256:" + "0" * 64, "baseline": {},
                "last_result": {
                    "task_id": "TASK-005", "allowed": False,
                    "reason_codes": ["OUT_OF_SCOPE_CHANGE"], "reasons": ["outside scope"],
                    "changes": [{"path": "other.md", "change_type": "created"}],
                    "out_of_scope_paths": ["other.md"], "missing_manifests": [],
                    "checked_tree_hash": "sha256:" + "1" * 64
                }
            }
            (root / ".agents" / "tasks" / "TASK-005.json").write_text(json.dumps(task), encoding="utf-8")
            (root / ".agents" / "snapshots" / "TASK-005.json").write_text(json.dumps(snapshot), encoding="utf-8")
            diagnostics = validate_project(root, model_policy_required=False)
            self.assertIn("SCOPE_CHECK_FAILED", [d.code for d in diagnostics])

    def test_review_ready_task_rejects_stale_persisted_scope_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("tasks", "messages", "decisions", "handoffs", "reports", "snapshots"):
                (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
            (root / "README.md").write_text("# Project\n", encoding="utf-8")
            task = {
                "task_id": "TASK-006", "title": "Stale scope", "owner": "worker-a",
                "status": "review_ready", "read_set": [], "write_set": ["README.md"],
                "impact_set": [], "core_impact_set": [], "depends_on": [],
                "acceptance_checks": [], "writing_lease": "lease-stale-scope",
                "source_write": True, "review_level": "standard"
            }
            snapshot = {
                "version": 1, "task_id": "TASK-006", "writing_lease": "lease-stale-scope",
                "write_set": ["README.md"], "review_level": "standard",
                "graph_fingerprint": "sha256:" + "0" * 64, "baseline": {},
                "last_result": {
                    "task_id": "TASK-006", "allowed": True,
                    "reason_codes": [], "reasons": [], "changes": [],
                    "out_of_scope_paths": [], "missing_manifests": [],
                    "checked_tree_hash": "sha256:" + "1" * 64
                }
            }
            (root / ".agents" / "tasks" / "TASK-006.json").write_text(json.dumps(task), encoding="utf-8")
            (root / ".agents" / "snapshots" / "TASK-006.json").write_text(json.dumps(snapshot), encoding="utf-8")
            diagnostics = validate_project(root, model_policy_required=False)
            self.assertIn("SCOPE_CHECK_STALE", [d.code for d in diagnostics])

    def test_task_owner_must_exist_in_model_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("tasks", "messages", "decisions", "handoffs", "reports"):
                (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
            source_policy = Path(__file__).resolve().parents[1] / "agent-models.json"
            shutil.copy2(source_policy, root / "agent-models.json")
            task = {
                "task_id": "TASK-001", "title": "Unknown owner", "owner": "unknown-worker",
                "status": "ready", "read_set": [], "write_set": ["output.md"],
                "impact_set": [], "core_impact_set": [], "depends_on": [],
                "acceptance_checks": [], "writing_lease": "lease-unknown", "review_level": "standard"
            }
            (root / ".agents" / "tasks" / "TASK-001.json").write_text(json.dumps(task), encoding="utf-8")
            diagnostics = validate_project(root)
            self.assertIn("UNKNOWN_TASK_OWNER", [d.code for d in diagnostics])

    def test_read_only_reviewer_cannot_own_source_write_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("tasks", "messages", "decisions", "handoffs", "reports"):
                (root / ".agents" / name).mkdir(parents=True, exist_ok=True)
            source_policy = Path(__file__).resolve().parents[1] / "agent-models.json"
            shutil.copy2(source_policy, root / "agent-models.json")
            task = {
                "task_id": "TASK-001", "title": "Reviewer edit", "owner": "independent-reviewer",
                "status": "ready", "read_set": [], "write_set": ["source.md"],
                "impact_set": [], "core_impact_set": [], "depends_on": [],
                "acceptance_checks": [], "writing_lease": "lease-review", "source_write": True,
                "review_level": "standard"
            }
            (root / ".agents" / "tasks" / "TASK-001.json").write_text(json.dumps(task), encoding="utf-8")
            diagnostics = validate_project(root)
            self.assertIn("ROLE_SOURCE_WRITE_NOT_ALLOWED", [d.code for d in diagnostics])


if __name__ == "__main__":
    unittest.main()


class ReviewEvidenceValidationTests(unittest.TestCase):
    def _root(self, path: Path, *, review_level: str = "standard") -> dict:
        for name in ("tasks", "messages", "decisions", "handoffs", "reports"):
            (path / ".agents" / name).mkdir(parents=True, exist_ok=True)
        (path / "README.md").write_text("# Reviewed project\n", encoding="utf-8")
        from cogem.evidence import review_tree_hash
        task = {
            "task_id": "TASK-020", "title": "Reviewed change", "owner": "worker-a",
            "status": "closed", "read_set": [], "write_set": ["README.md"],
            "impact_set": [], "core_impact_set": [], "depends_on": [],
            "acceptance_checks": ["tests"], "writing_lease": "lease-20", "source_write": True,
            "review_level": review_level, "review_tree_hash": review_tree_hash(path)
        }
        (path / ".agents" / "tasks" / "TASK-020.json").write_text(json.dumps(task), encoding="utf-8")
        snapshot = {
            "version": 1,
            "task_id": "TASK-020",
            "writing_lease": "lease-20",
            "write_set": ["README.md"],
            "review_level": review_level,
            "graph_fingerprint": "sha256:" + "0" * 64,
            "baseline": {},
            "last_result": {
                "task_id": "TASK-020",
                "allowed": True,
                "reason_codes": [],
                "reasons": [],
                "changes": [{"path": "README.md", "change_type": "modified"}],
                "out_of_scope_paths": [],
                "missing_manifests": [],
                "checked_tree_hash": task["review_tree_hash"]
            }
        }
        (path / ".agents" / "snapshots").mkdir(parents=True, exist_ok=True)
        (path / ".agents" / "snapshots" / "TASK-020.json").write_text(json.dumps(snapshot), encoding="utf-8")
        return task

    def _report(self, root: Path, *, kind: str, pass_index: int, prompt_mode: str, tree_hash: str) -> None:
        report = {
            "report_id": f"REPORT-02{pass_index}", "agent_id": "independent-reviewer", "task_id": "TASK-020",
            "kind": kind, "status": "pass", "summary": "Review passed", "evidence": ["tests"],
            "created_at": f"2026-07-16T12:0{pass_index}:00+09:00",
            "review_proof": {
                "engine": "antigravity-preview-05-2026", "session_id": f"session-{pass_index}",
                "fresh_context": True, "permissions": "read-only", "source_write_performed": False,
                "reviewed_tree_hash": tree_hash, "prior_findings_provided": False,
                "prompt_mode": prompt_mode, "pass_index": pass_index
            }
        }
        (root / ".agents" / "reports" / f"REPORT-02{pass_index}.json").write_text(json.dumps(report), encoding="utf-8")

    def test_closed_task_requires_independent_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            diagnostics = validate_project(root, model_policy_required=False)
            self.assertIn("MISSING_INDEPENDENT_REVIEW", [d.code for d in diagnostics])

    def test_high_risk_task_requires_second_adversarial_review(self):
        from cogem.evidence import review_tree_hash
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = self._root(root, review_level="high-risk")
            digest = task["review_tree_hash"]
            self._report(root, kind="independent-review", pass_index=1, prompt_mode="independent", tree_hash=digest)
            diagnostics = validate_project(root, model_policy_required=False)
            self.assertIn("MISSING_ADVERSARIAL_REVIEW", [d.code for d in diagnostics])

    def test_matching_independent_and_adversarial_proofs_pass(self):
        from cogem.evidence import review_tree_hash
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = self._root(root, review_level="high-risk")
            digest = task["review_tree_hash"]
            self._report(root, kind="independent-review", pass_index=1, prompt_mode="independent", tree_hash=digest)
            self._report(root, kind="adversarial-review", pass_index=2, prompt_mode="adversarial", tree_hash=digest)
            diagnostics = validate_project(root, model_policy_required=False)
            errors = [d for d in diagnostics if d.severity == "error"]
            self.assertEqual(errors, [])

    def test_closed_task_review_remains_valid_after_later_source_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = self._root(root)
            self._report(root, kind="independent-review", pass_index=1, prompt_mode="independent", tree_hash=task["review_tree_hash"])
            (root / "later.md").write_text("# Later approved work\n", encoding="utf-8")
            diagnostics = validate_project(root, model_policy_required=False)
            codes = [d.code for d in diagnostics]
            self.assertNotIn("REVIEW_TREE_HASH_MISMATCH", codes)
            self.assertNotIn("MISSING_INDEPENDENT_REVIEW", codes)

    def test_integrated_task_hash_must_match_current_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = self._root(root)
            task["status"] = "integrated"
            (root / ".agents" / "tasks" / "TASK-020.json").write_text(json.dumps(task), encoding="utf-8")
            self._report(root, kind="independent-review", pass_index=1, prompt_mode="independent", tree_hash=task["review_tree_hash"])
            (root / "changed-before-close.md").write_text("# Changed\n", encoding="utf-8")
            diagnostics = validate_project(root, model_policy_required=False)
            self.assertIn("TASK_REVIEW_TREE_STALE", [d.code for d in diagnostics])

    def test_stale_review_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._root(root)
            self._report(root, kind="independent-review", pass_index=1, prompt_mode="independent", tree_hash="sha256:" + "0" * 64)
            diagnostics = validate_project(root, model_policy_required=False)
            self.assertIn("REVIEW_TREE_HASH_MISMATCH", [d.code for d in diagnostics])
