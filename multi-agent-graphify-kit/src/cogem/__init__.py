"""Cogem: provider-neutral coordination and graph analysis for multi-agent work."""

from .contracts import (
    AgentMessage,
    ContractError,
    DecisionRecord,
    GoalCriterion,
    GoalRecord,
    HandoffRecord,
    ReportRecord,
    ReviewProof,
    TaskRecord,
)
from .goal import GoalCheckResult
from .scope import ScopeChange, ScopeCheckResult
from .state import CogemState, load_state

__all__ = [
    "AgentMessage",
    "CogemState",
    "ContractError",
    "DecisionRecord",
    "GoalCheckResult",
    "GoalCriterion",
    "GoalRecord",
    "HandoffRecord",
    "ReportRecord",
    "ReviewProof",
    "ScopeChange",
    "ScopeCheckResult",
    "TaskRecord",
    "load_state",
]

__version__ = "5.0.0"
