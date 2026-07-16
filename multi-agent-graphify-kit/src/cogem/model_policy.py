"""Capability-profile execution-engine routing for Cogem roles.

The public file and compatibility symbols retain ``model`` terminology, while
Cogem 4.0 routes both ordinary LLM models and managed agents such as
Antigravity.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Mapping


class ModelPolicyError(ValueError):
    """Raised when an execution-engine profile or role policy is invalid."""


PERMISSIONS = ("coordination-write", "scoped-write", "generated-write", "read-only")
ENGINE_KINDS = ("model", "managed-agent")
REVIEW_ROLES = {"independent-reviewer"}
_TRUE_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class EngineProfile:
    name: str
    engine_env: str
    provider: str
    engine_kind: str
    deliberation: str
    required_capabilities: tuple[str, ...]
    fallback_profile: str | None

    @property
    def model_env(self) -> str:
        """Backward-compatible alias for Cogem v1 callers."""
        return self.engine_env


@dataclass(frozen=True, slots=True)
class RoleEnginePolicy:
    role_id: str
    profile: str
    permissions: str
    fresh_context: bool
    optional: bool
    distinct_from_roles: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HighRiskSecondPass:
    enabled: bool
    reuse_role: bool
    fresh_context: bool
    carry_forward_prior_findings: bool
    prompt_mode: str


@dataclass(frozen=True, slots=True)
class DegradedReviewFallback:
    engine_env: str
    opt_in_env: str
    mode: str
    provider: str
    engine_kind: str
    deliberation: str


@dataclass(frozen=True, slots=True)
class ReviewStrategy:
    required_role: str
    high_risk_second_pass: HighRiskSecondPass
    degraded_fallback: DegradedReviewFallback | None


@dataclass(frozen=True, slots=True)
class ModelPolicy:
    profiles: dict[str, EngineProfile]
    roles: dict[str, RoleEnginePolicy]
    review_strategy: ReviewStrategy
    allow_profile_fallback: bool
    enforce_engine_diversity: bool
    max_concurrent_source_writers: int

    @property
    def enforce_model_diversity(self) -> bool:
        """Backward-compatible alias for Cogem v1 callers."""
        return self.enforce_engine_diversity


@dataclass(frozen=True, slots=True)
class ResolvedRoleEngine:
    role_id: str
    profile: str
    engine_id: str
    provider: str
    engine_kind: str
    deliberation: str
    permissions: str
    fresh_context: bool
    required_capabilities: tuple[str, ...]
    degraded_independence: bool = False
    review_mode: str | None = None

    @property
    def model_id(self) -> str:
        """Backward-compatible alias for Cogem v1 callers."""
        return self.engine_id


# Compatibility names retained for callers that imported v1 symbols.
ModelProfile = EngineProfile
RoleModelPolicy = RoleEnginePolicy
ResolvedRoleModel = ResolvedRoleEngine


def _nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelPolicyError(f"{label} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ModelPolicyError(f"{label} must be an array of non-empty strings")
    normalized = tuple(item.strip() for item in value)
    if len(normalized) != len(set(normalized)):
        raise ModelPolicyError(f"{label} must not contain duplicates")
    return normalized


def _boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ModelPolicyError(f"{label} must be a boolean")
    return value


def _env_enabled(environment: Mapping[str, str], name: str) -> bool:
    return environment.get(name, "").strip().lower() in _TRUE_VALUES


def _parse_review_strategy(raw: Any, roles: Mapping[str, RoleEnginePolicy]) -> ReviewStrategy:
    if not isinstance(raw, Mapping):
        raise ModelPolicyError("review_strategy must be an object")

    required_role = _nonempty_string(raw.get("required_role"), "review_strategy.required_role")
    role = roles.get(required_role)
    if role is None:
        raise ModelPolicyError(f"review_strategy.required_role references missing role {required_role!r}")
    if role.permissions != "read-only" or not role.fresh_context or role.optional:
        raise ModelPolicyError("required review role must be non-optional, read-only, and use a fresh context")

    raw_second = raw.get("high_risk_second_pass")
    if not isinstance(raw_second, Mapping):
        raise ModelPolicyError("review_strategy.high_risk_second_pass must be an object")
    second = HighRiskSecondPass(
        enabled=_boolean(raw_second.get("enabled"), "review_strategy.high_risk_second_pass.enabled"),
        reuse_role=_boolean(raw_second.get("reuse_role"), "review_strategy.high_risk_second_pass.reuse_role"),
        fresh_context=_boolean(raw_second.get("fresh_context"), "review_strategy.high_risk_second_pass.fresh_context"),
        carry_forward_prior_findings=_boolean(
            raw_second.get("carry_forward_prior_findings"),
            "review_strategy.high_risk_second_pass.carry_forward_prior_findings",
        ),
        prompt_mode=_nonempty_string(
            raw_second.get("prompt_mode"),
            "review_strategy.high_risk_second_pass.prompt_mode",
        ),
    )
    if second.enabled and (
        not second.reuse_role
        or not second.fresh_context
        or second.carry_forward_prior_findings
        or second.prompt_mode != "adversarial"
    ):
        raise ModelPolicyError(
            "high-risk second pass must reuse the required reviewer role in a fresh context "
            "without prior findings and use adversarial prompt mode"
        )

    raw_fallback = raw.get("degraded_fallback")
    fallback: DegradedReviewFallback | None
    if raw_fallback is None:
        fallback = None
    else:
        if not isinstance(raw_fallback, Mapping):
            raise ModelPolicyError("review_strategy.degraded_fallback must be an object or null")
        engine_kind = _nonempty_string(
            raw_fallback.get("engine_kind"),
            "review_strategy.degraded_fallback.engine_kind",
        )
        if engine_kind not in ENGINE_KINDS:
            raise ModelPolicyError(
                "review_strategy.degraded_fallback.engine_kind must be one of "
                + ", ".join(ENGINE_KINDS)
            )
        fallback = DegradedReviewFallback(
            engine_env=_nonempty_string(
                raw_fallback.get("engine_env"),
                "review_strategy.degraded_fallback.engine_env",
            ),
            opt_in_env=_nonempty_string(
                raw_fallback.get("opt_in_env"),
                "review_strategy.degraded_fallback.opt_in_env",
            ),
            mode=_nonempty_string(raw_fallback.get("mode"), "review_strategy.degraded_fallback.mode"),
            provider=_nonempty_string(
                raw_fallback.get("provider"),
                "review_strategy.degraded_fallback.provider",
            ),
            engine_kind=engine_kind,
            deliberation=_nonempty_string(
                raw_fallback.get("deliberation"),
                "review_strategy.degraded_fallback.deliberation",
            ),
        )

    return ReviewStrategy(
        required_role=required_role,
        high_risk_second_pass=second,
        degraded_fallback=fallback,
    )


def load_model_policy_data(raw: Mapping[str, Any]) -> ModelPolicy:
    if not isinstance(raw, Mapping):
        raise ModelPolicyError("model policy must be a JSON object")
    if raw.get("version") != 2:
        raise ModelPolicyError("model policy version must be 2")

    raw_profiles = raw.get("profiles")
    raw_roles = raw.get("roles")
    if not isinstance(raw_profiles, Mapping) or not raw_profiles:
        raise ModelPolicyError("profiles must be a non-empty object")
    if not isinstance(raw_roles, Mapping) or not raw_roles:
        raise ModelPolicyError("roles must be a non-empty object")

    profiles: dict[str, EngineProfile] = {}
    for name, value in raw_profiles.items():
        if not isinstance(value, Mapping):
            raise ModelPolicyError(f"profile {name!r} must be an object")
        profile_name = _nonempty_string(name, "profile name")
        fallback = value.get("fallback_profile")
        if fallback is not None:
            fallback = _nonempty_string(fallback, f"profiles.{name}.fallback_profile")
        engine_kind = _nonempty_string(value.get("engine_kind"), f"profiles.{name}.engine_kind")
        if engine_kind not in ENGINE_KINDS:
            raise ModelPolicyError(f"profiles.{name}.engine_kind must be one of {', '.join(ENGINE_KINDS)}")
        profiles[profile_name] = EngineProfile(
            name=profile_name,
            engine_env=_nonempty_string(value.get("engine_env"), f"profiles.{name}.engine_env"),
            provider=_nonempty_string(value.get("provider"), f"profiles.{name}.provider"),
            engine_kind=engine_kind,
            deliberation=_nonempty_string(value.get("deliberation"), f"profiles.{name}.deliberation"),
            required_capabilities=_string_list(
                value.get("required_capabilities", []),
                f"profiles.{name}.required_capabilities",
            ),
            fallback_profile=fallback,
        )
    for profile in profiles.values():
        if profile.fallback_profile is not None and profile.fallback_profile not in profiles:
            raise ModelPolicyError(
                f"profile {profile.name!r} references missing fallback profile {profile.fallback_profile!r}"
            )

    roles: dict[str, RoleEnginePolicy] = {}
    for name, value in raw_roles.items():
        if not isinstance(value, Mapping):
            raise ModelPolicyError(f"role {name!r} must be an object")
        role_id = _nonempty_string(name, "role name")
        profile = _nonempty_string(value.get("profile"), f"roles.{name}.profile")
        if profile not in profiles:
            raise ModelPolicyError(f"role {role_id!r} references missing profile {profile!r}")
        permissions = _nonempty_string(value.get("permissions"), f"roles.{name}.permissions")
        if permissions not in PERMISSIONS:
            raise ModelPolicyError(f"roles.{name}.permissions must be one of {', '.join(PERMISSIONS)}")
        fresh_context = _boolean(value.get("fresh_context"), f"roles.{name}.fresh_context")
        optional = _boolean(value.get("optional"), f"roles.{name}.optional")
        distinct = _string_list(value.get("distinct_from_roles", []), f"roles.{name}.distinct_from_roles")
        if role_id in REVIEW_ROLES and (permissions != "read-only" or not fresh_context or optional):
            raise ModelPolicyError(
                f"{role_id} must be non-optional, use read-only permissions, and start with a fresh context"
            )
        roles[role_id] = RoleEnginePolicy(
            role_id=role_id,
            profile=profile,
            permissions=permissions,
            fresh_context=fresh_context,
            optional=optional,
            distinct_from_roles=distinct,
        )

    for role_id, role in roles.items():
        for other_role_id in role.distinct_from_roles:
            if other_role_id not in roles:
                raise ModelPolicyError(
                    f"role {role_id!r} requires diversity from missing role {other_role_id!r}"
                )
            if other_role_id == role_id:
                raise ModelPolicyError(f"role {role_id!r} cannot require diversity from itself")

    review_strategy = _parse_review_strategy(raw.get("review_strategy"), roles)

    allow_fallback = raw.get("allow_profile_fallback")
    enforce_diversity = raw.get("enforce_engine_diversity")
    max_writers = raw.get("max_concurrent_source_writers")
    if not isinstance(allow_fallback, bool):
        raise ModelPolicyError("allow_profile_fallback must be a boolean")
    if not isinstance(enforce_diversity, bool):
        raise ModelPolicyError("enforce_engine_diversity must be a boolean")
    if not isinstance(max_writers, int) or isinstance(max_writers, bool) or max_writers < 1:
        raise ModelPolicyError("max_concurrent_source_writers must be a positive integer")

    return ModelPolicy(
        profiles=dict(sorted(profiles.items())),
        roles=dict(sorted(roles.items())),
        review_strategy=review_strategy,
        allow_profile_fallback=allow_fallback,
        enforce_engine_diversity=enforce_diversity,
        max_concurrent_source_writers=max_writers,
    )


def load_model_policy(path: Path) -> ModelPolicy:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ModelPolicyError(f"model policy file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ModelPolicyError(
            f"invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    return load_model_policy_data(raw)


def _resolve_profile_engine(
    profile_name: str,
    policy: ModelPolicy,
    environment: Mapping[str, str],
    visited: set[str] | None = None,
) -> tuple[str, EngineProfile] | None:
    visited = set() if visited is None else set(visited)
    if profile_name in visited:
        raise ModelPolicyError(f"engine profile fallback cycle detected at {profile_name!r}")
    visited.add(profile_name)
    profile = policy.profiles[profile_name]
    engine_id = environment.get(profile.engine_env, "").strip()
    if engine_id:
        return engine_id, profile
    if policy.allow_profile_fallback and profile.fallback_profile:
        return _resolve_profile_engine(profile.fallback_profile, policy, environment, visited)
    return None


def _resolve_degraded_reviewer(
    role_id: str,
    policy: ModelPolicy,
    environment: Mapping[str, str],
) -> ResolvedRoleEngine | None:
    strategy = policy.review_strategy
    fallback = strategy.degraded_fallback
    if role_id != strategy.required_role or fallback is None:
        return None
    if not _env_enabled(environment, fallback.opt_in_env):
        return None
    engine_id = environment.get(fallback.engine_env, "").strip()
    if not engine_id:
        raise ModelPolicyError(
            f"degraded review is enabled but no fallback engine is set; set {fallback.engine_env}"
        )
    role = policy.roles[role_id]
    profile = policy.profiles[role.profile]
    return ResolvedRoleEngine(
        role_id=role_id,
        profile=profile.name,
        engine_id=engine_id,
        provider=fallback.provider,
        engine_kind=fallback.engine_kind,
        deliberation=fallback.deliberation,
        permissions=role.permissions,
        fresh_context=role.fresh_context,
        required_capabilities=profile.required_capabilities,
        degraded_independence=True,
        review_mode=fallback.mode,
    )


def resolve_role_engines(
    policy: ModelPolicy,
    environment: Mapping[str, str] | None = None,
) -> dict[str, ResolvedRoleEngine]:
    env = os.environ if environment is None else environment
    resolved: dict[str, ResolvedRoleEngine] = {}
    for role_id, role in policy.roles.items():
        result = _resolve_profile_engine(role.profile, policy, env)
        if result is None:
            degraded = _resolve_degraded_reviewer(role_id, policy, env)
            if degraded is not None:
                resolved[role_id] = degraded
                continue
            env_name = policy.profiles[role.profile].engine_env
            if role.optional:
                continue
            raise ModelPolicyError(f"required role {role_id!r} has no execution engine; set {env_name}")
        engine_id, profile = result
        resolved[role_id] = ResolvedRoleEngine(
            role_id=role_id,
            profile=profile.name,
            engine_id=engine_id,
            provider=profile.provider,
            engine_kind=profile.engine_kind,
            deliberation=profile.deliberation,
            permissions=role.permissions,
            fresh_context=role.fresh_context,
            required_capabilities=profile.required_capabilities,
            review_mode="independent" if role_id == policy.review_strategy.required_role else None,
        )

    if policy.enforce_engine_diversity:
        for role_id, role in policy.roles.items():
            current = resolved.get(role_id)
            if current is None or current.degraded_independence:
                continue
            for other_role_id in role.distinct_from_roles:
                other = resolved.get(other_role_id)
                if other is not None and other.engine_id == current.engine_id:
                    raise ModelPolicyError(
                        f"execution-engine diversity violation: {role_id} and {other_role_id} "
                        "resolve to the same engine"
                    )
    return resolved


def _resolved_for_plan(
    role_id: str,
    policy: ModelPolicy,
    environment: Mapping[str, str],
) -> ResolvedRoleEngine | None:
    role = policy.roles[role_id]
    result = _resolve_profile_engine(role.profile, policy, environment)
    if result is None:
        return _resolve_degraded_reviewer(role_id, policy, environment)
    engine_id, profile = result
    return ResolvedRoleEngine(
        role_id=role_id,
        profile=profile.name,
        engine_id=engine_id,
        provider=profile.provider,
        engine_kind=profile.engine_kind,
        deliberation=profile.deliberation,
        permissions=role.permissions,
        fresh_context=role.fresh_context,
        required_capabilities=profile.required_capabilities,
        review_mode="independent" if role_id == policy.review_strategy.required_role else None,
    )


def execution_plan(
    policy: ModelPolicy,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Return a credential-safe role and review execution plan."""
    env = os.environ if environment is None else environment
    second = policy.review_strategy.high_risk_second_pass
    rows: list[dict[str, Any]] = []
    for role_id, role in policy.roles.items():
        profile = policy.profiles[role.profile]
        resolved = _resolved_for_plan(role_id, policy, env)
        review_passes: list[str] = []
        if role_id == policy.review_strategy.required_role:
            review_passes.append("independent")
            if second.enabled:
                review_passes.append("adversarial")
        rows.append(
            {
                "role": role_id,
                "profile": role.profile,
                "provider": resolved.provider if resolved else profile.provider,
                "engine_kind": resolved.engine_kind if resolved else profile.engine_kind,
                "deliberation": resolved.deliberation if resolved else profile.deliberation,
                "permissions": role.permissions,
                "fresh_context": role.fresh_context,
                "optional": role.optional,
                "engine_env": profile.engine_env,
                "resolved": resolved is not None,
                "effective_profile": resolved.profile if resolved else None,
                "degraded_independence": resolved.degraded_independence if resolved else False,
                "review_mode": resolved.review_mode if resolved else None,
                "review_passes": sorted(review_passes),
                "required_capabilities": list(profile.required_capabilities),
            }
        )

    fallback = policy.review_strategy.degraded_fallback
    return {
        "roles": rows,
        "review_strategy": {
            "required_role": policy.review_strategy.required_role,
            "high_risk_second_pass": {
                "enabled": second.enabled,
                "reuse_role": second.reuse_role,
                "fresh_context": second.fresh_context,
                "carry_forward_prior_findings": second.carry_forward_prior_findings,
                "prompt_mode": second.prompt_mode,
            },
            "degraded_fallback": None
            if fallback is None
            else {
                "engine_env": fallback.engine_env,
                "opt_in_env": fallback.opt_in_env,
                "mode": fallback.mode,
                "provider": fallback.provider,
                "engine_kind": fallback.engine_kind,
                "deliberation": fallback.deliberation,
            },
        },
    }


def engine_plan(
    policy: ModelPolicy,
    environment: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Return only role rows for CLI compatibility and compact display."""
    return execution_plan(policy, environment)["roles"]


# Cogem v1 compatibility wrappers.
resolve_role_models = resolve_role_engines
model_plan = engine_plan
