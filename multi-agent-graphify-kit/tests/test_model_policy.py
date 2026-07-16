import os
import unittest
from unittest.mock import patch

from cogem.model_policy import (
    ModelPolicyError,
    execution_plan,
    load_model_policy_data,
    resolve_role_engines,
)


POLICY = {
    "version": 2,
    "profiles": {
        "reasoning-high": {
            "engine_env": "COGEM_COORDINATOR_ENGINE",
            "provider": "openai",
            "engine_kind": "model",
            "deliberation": "max",
            "required_capabilities": ["structured_output", "tool_use", "long_context"],
            "fallback_profile": None,
        },
        "balanced": {
            "engine_env": "COGEM_BALANCED_ENGINE",
            "provider": "openai",
            "engine_kind": "model",
            "deliberation": "high",
            "required_capabilities": ["structured_output", "tool_use"],
            "fallback_profile": None,
        },
        "review-high": {
            "engine_env": "COGEM_REVIEW_ENGINE",
            "provider": "google",
            "engine_kind": "managed-agent",
            "deliberation": "managed",
            "required_capabilities": ["adversarial_review", "cross_file_consistency"],
            "fallback_profile": None,
        },
    },
    "roles": {
        "coordinator": {
            "profile": "reasoning-high",
            "permissions": "coordination-write",
            "fresh_context": False,
            "optional": False,
            "distinct_from_roles": [],
        },
        "graph-analyst": {
            "profile": "balanced",
            "permissions": "generated-write",
            "fresh_context": True,
            "optional": False,
            "distinct_from_roles": [],
        },
        "worker-a": {
            "profile": "balanced",
            "permissions": "scoped-write",
            "fresh_context": True,
            "optional": False,
            "distinct_from_roles": [],
        },
        "worker-b": {
            "profile": "balanced",
            "permissions": "scoped-write",
            "fresh_context": True,
            "optional": False,
            "distinct_from_roles": [],
        },
        "independent-reviewer": {
            "profile": "review-high",
            "permissions": "read-only",
            "fresh_context": True,
            "optional": False,
            "distinct_from_roles": ["coordinator", "graph-analyst", "worker-a", "worker-b"],
        },
    },
    "review_strategy": {
        "required_role": "independent-reviewer",
        "high_risk_second_pass": {
            "enabled": True,
            "reuse_role": True,
            "fresh_context": True,
            "carry_forward_prior_findings": False,
            "prompt_mode": "adversarial",
        },
        "degraded_fallback": {
            "engine_env": "COGEM_REVIEW_FALLBACK_ENGINE",
            "opt_in_env": "COGEM_ALLOW_DEGRADED_REVIEW",
            "mode": "same-provider-fallback",
            "provider": "openai",
            "engine_kind": "model",
            "deliberation": "max",
        },
    },
    "allow_profile_fallback": False,
    "enforce_engine_diversity": True,
    "max_concurrent_source_writers": 2,
}


class ModelPolicyTests(unittest.TestCase):
    def test_resolves_gpt_and_antigravity_engines(self):
        policy = load_model_policy_data(POLICY)
        with patch.dict(
            os.environ,
            {
                "COGEM_COORDINATOR_ENGINE": "gpt-5.6-sol",
                "COGEM_BALANCED_ENGINE": "gpt-5.6-terra",
                "COGEM_REVIEW_ENGINE": "antigravity-preview-05-2026",
            },
            clear=True,
        ):
            resolved = resolve_role_engines(policy)
        self.assertEqual(resolved["coordinator"].engine_id, "gpt-5.6-sol")
        self.assertEqual(resolved["worker-a"].engine_id, "gpt-5.6-terra")
        reviewer = resolved["independent-reviewer"]
        self.assertEqual(reviewer.engine_id, "antigravity-preview-05-2026")
        self.assertEqual(reviewer.engine_kind, "managed-agent")
        self.assertFalse(reviewer.degraded_independence)
        self.assertEqual(reviewer.review_mode, "independent")
        self.assertIsNone(resolved["coordinator"].review_mode)

    def test_missing_required_review_engine_is_an_error_without_explicit_fallback(self):
        policy = load_model_policy_data(POLICY)
        with patch.dict(
            os.environ,
            {
                "COGEM_COORDINATOR_ENGINE": "gpt-5.6-sol",
                "COGEM_BALANCED_ENGINE": "gpt-5.6-terra",
                "COGEM_REVIEW_FALLBACK_ENGINE": "gpt-5.6-sol",
                "COGEM_ALLOW_DEGRADED_REVIEW": "false",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(ModelPolicyError, "COGEM_REVIEW_ENGINE"):
                resolve_role_engines(policy)

    def test_explicit_gpt_fallback_is_resolved_as_degraded_independence(self):
        policy = load_model_policy_data(POLICY)
        with patch.dict(
            os.environ,
            {
                "COGEM_COORDINATOR_ENGINE": "gpt-5.6-sol",
                "COGEM_BALANCED_ENGINE": "gpt-5.6-terra",
                "COGEM_REVIEW_FALLBACK_ENGINE": "gpt-5.6-sol",
                "COGEM_ALLOW_DEGRADED_REVIEW": "true",
            },
            clear=True,
        ):
            resolved = resolve_role_engines(policy)
        reviewer = resolved["independent-reviewer"]
        self.assertEqual(reviewer.engine_id, "gpt-5.6-sol")
        self.assertTrue(reviewer.degraded_independence)
        self.assertEqual(reviewer.review_mode, "same-provider-fallback")

    def test_review_role_requires_fresh_read_only_context(self):
        invalid = {
            **POLICY,
            "roles": {
                **POLICY["roles"],
                "independent-reviewer": {
                    **POLICY["roles"]["independent-reviewer"],
                    "permissions": "scoped-write",
                    "fresh_context": False,
                },
            },
        }
        with self.assertRaisesRegex(ModelPolicyError, "independent-reviewer"):
            load_model_policy_data(invalid)

    def test_high_risk_second_pass_must_be_fresh_and_not_inherit_prior_findings(self):
        invalid = {
            **POLICY,
            "review_strategy": {
                **POLICY["review_strategy"],
                "high_risk_second_pass": {
                    **POLICY["review_strategy"]["high_risk_second_pass"],
                    "fresh_context": False,
                    "carry_forward_prior_findings": True,
                },
            },
        }
        with self.assertRaisesRegex(ModelPolicyError, "high-risk second pass"):
            load_model_policy_data(invalid)

    def test_enforced_engine_diversity_rejects_same_primary_engine(self):
        policy = load_model_policy_data(POLICY)
        with patch.dict(
            os.environ,
            {
                "COGEM_COORDINATOR_ENGINE": "shared-engine",
                "COGEM_BALANCED_ENGINE": "shared-engine",
                "COGEM_REVIEW_ENGINE": "shared-engine",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(ModelPolicyError, "diversity"):
                resolve_role_engines(policy)

    def test_execution_plan_contains_five_roles_and_second_review_pass(self):
        policy = load_model_policy_data(POLICY)
        plan = execution_plan(policy, environment={})
        self.assertEqual(len(plan["roles"]), 5)
        self.assertEqual(plan["review_strategy"]["required_role"], "independent-reviewer")
        self.assertTrue(plan["review_strategy"]["high_risk_second_pass"]["enabled"])
        reviewer = next(row for row in plan["roles"] if row["role"] == "independent-reviewer")
        self.assertEqual(reviewer["review_passes"], ["adversarial", "independent"])
        self.assertNotIn("antigravity-reviewer", {row["role"] for row in plan["roles"]})


if __name__ == "__main__":
    unittest.main()
