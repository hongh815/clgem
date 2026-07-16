import json
import unittest
from pathlib import Path

from cogem.skill_policy import validate_skills


ROOT = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def test_required_distribution_files_exist(self):
        required = [
            "README.md", "AGENTS.md", "Comm.md", "cogem.config.json", "agent-models.json",
            "docs/skill-authoring.md", "docs/release-notes-3.0.0.md", "docs/release-notes-4.0.0.md",
            "docs/release-notes-5.0.0.md",
            "model-presets/README.md", "model-presets/plan-a-gpt-antigravity.env",
            "skills/cogem/SKILL.md", "skills/cogem/manifest.txt", "skills/cogem/agents/openai.yaml",
            "skills/cogem/references/agent-model.md", "skills/cogem/references/communication-protocol.md",
            "skills/cogem/references/graph-model.md", "skills/cogem/references/leader-loop.md",
            "skills/cogem/references/parallel-safety.md", "skills/cogem/schemas/goal.schema.json",
            "skills/cogem/schemas/scope-snapshot.schema.json",
            "src/cogem/goal.py", "src/cogem/task_policy.py", "src/cogem/scope.py", "src/cogem/skill_init.py",
            ".agents/goals/.gitkeep", ".agents/snapshots/.gitkeep",
            "scripts/cogem.py", "scripts/run_tests.py", "scripts/package_kit.py", "pyproject.toml", "Makefile",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual(missing, [])

    def test_every_skill_obeys_generic_authoring_policy(self):
        self.assertEqual(validate_skills(ROOT), [])

    def test_all_json_files_parse(self):
        paths = [
            path for path in ROOT.rglob("*.json")
            if ".graph" not in path.parts and "__pycache__" not in path.parts
        ]
        self.assertGreaterEqual(len(paths), 10)
        for path in paths:
            with self.subTest(path=path):
                json.loads(path.read_text(encoding="utf-8"))

    def test_review_proof_schema_requires_an_object_when_present(self):
        schema = json.loads((ROOT / "skills/cogem/schemas/report.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["review_proof"]["type"], "object")

    def test_review_proof_is_publicly_exported(self):
        init = (ROOT / "src/cogem/__init__.py").read_text(encoding="utf-8")
        self.assertIn("ReviewProof", init)

    def test_scope_contract_is_publicly_exported(self):
        init = (ROOT / "src/cogem/__init__.py").read_text(encoding="utf-8")
        self.assertIn("ScopeChange", init)
        self.assertIn("ScopeCheckResult", init)

    def test_documentation_uses_cogem_name(self):
        for path in [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "skills/cogem/SKILL.md"]:
            with self.subTest(path=path):
                self.assertIn("Cogem", path.read_text(encoding="utf-8"))

    def test_version_is_5_0_0(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        init = (ROOT / "src/cogem/__init__.py").read_text(encoding="utf-8")
        self.assertIn('version = "5.0.0"', pyproject)
        self.assertIn('__version__ = "5.0.0"', init)

    def test_task_schema_requires_explicit_review_level(self):
        schema = json.loads((ROOT / "skills/cogem/schemas/task.schema.json").read_text(encoding="utf-8"))
        self.assertIn("review_level", schema["required"])
        self.assertNotIn("default", schema["properties"]["review_level"])

    def test_scope_snapshot_schema_has_a_closed_result_contract(self):
        schema = json.loads((ROOT / "skills/cogem/schemas/scope-snapshot.schema.json").read_text(encoding="utf-8"))
        result_variants = schema["properties"]["last_result"]["oneOf"]
        result = next(item for item in result_variants if item.get("type") == "object")
        self.assertFalse(result["additionalProperties"])
        self.assertIn("checked_tree_hash", result["required"])
        self.assertEqual(
            result["properties"]["changes"]["items"]["properties"]["change_type"]["enum"],
            ["created", "modified", "deleted"],
        )

    def test_release_state_is_bootstrap_clean(self):
        for name in ("goals", "tasks", "messages", "decisions", "handoffs", "reports", "snapshots"):
            records = list((ROOT / ".agents" / name).glob("*.json"))
            self.assertEqual(records, [], f"release contains live {name} records")

    def test_comm_is_unambiguous_bootstrap_snapshot(self):
        text = (ROOT / "Comm.md").read_text(encoding="utf-8").lower()
        self.assertIn("bootstrap", text)
        self.assertIn("not generated", text)
        self.assertIn("not run", text)
        self.assertNotIn("report-001", text)

    def test_plan_a_has_exactly_five_roles_with_antigravity_as_required_reviewer(self):
        policy = json.loads((ROOT / "agent-models.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["version"], 2)
        self.assertEqual(
            set(policy["roles"]),
            {"coordinator", "graph-analyst", "worker-a", "worker-b", "independent-reviewer"},
        )
        self.assertEqual(set(policy["profiles"]), {"reasoning-high", "balanced", "review-high"})
        self.assertEqual(policy["max_concurrent_source_writers"], 2)
        self.assertTrue(policy["enforce_engine_diversity"])
        reviewer = policy["roles"]["independent-reviewer"]
        self.assertEqual(reviewer["permissions"], "read-only")
        self.assertTrue(reviewer["fresh_context"])
        self.assertFalse(reviewer["optional"])
        self.assertEqual(policy["profiles"]["review-high"]["engine_kind"], "managed-agent")
        self.assertEqual(policy["profiles"]["review-high"]["engine_env"], "COGEM_REVIEW_ENGINE")
        strategy = policy["review_strategy"]
        self.assertEqual(strategy["required_role"], "independent-reviewer")
        self.assertTrue(strategy["high_risk_second_pass"]["reuse_role"])

    def test_recommended_gpt_antigravity_preset_is_exact(self):
        preset = ROOT / "model-presets/plan-a-gpt-antigravity.env"
        values = {}
        for raw_line in preset.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            values[key] = value
        self.assertEqual(values, {
            "COGEM_COORDINATOR_ENGINE": "gpt-5.6-sol",
            "COGEM_BALANCED_ENGINE": "gpt-5.6-terra",
            "COGEM_REVIEW_ENGINE": "antigravity-preview-05-2026",
            "COGEM_REVIEW_FALLBACK_ENGINE": "gpt-5.6-sol",
            "COGEM_ALLOW_DEGRADED_REVIEW": "false",
        })

    def test_published_files_remove_old_reviewer_configuration(self):
        paths = [
            ROOT / "agent-models.json", ROOT / ".env.example", ROOT / "README.md", ROOT / "AGENTS.md",
            ROOT / "docs/agent-model.md", ROOT / "docs/agent-roles.md", ROOT / "docs/execution-workflow.md",
            ROOT / "skills/cogem/SKILL.md", ROOT / "skills/cogem/references/agent-model.md",
            ROOT / "model-presets/README.md", ROOT / "model-presets/plan-a-gpt-antigravity.env",
        ]
        published_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in paths).lower()
        for forbidden in ("gpt-5.5", "claude", "anthropic", "antigravity-reviewer", "cogem_model_adversarial_high"):
            self.assertNotIn(forbidden, published_text)
        self.assertIn("high-risk second pass", published_text)
        self.assertIn("antigravity-preview-05-2026", published_text)


if __name__ == "__main__":
    unittest.main()
