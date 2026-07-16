import tempfile
import unittest
from pathlib import Path

from cogem.comm import render_comm, write_comm
from cogem.contracts import AgentMessage, DecisionRecord, GoalRecord, HandoffRecord, TaskRecord
from cogem.state import CogemState


class CommRendererTests(unittest.TestCase):
    def test_render_comm_is_deterministic_and_contains_operational_sections(self):
        task = TaskRecord.from_dict({
            "task_id": "TASK-002", "title": "Build graph", "owner": "graph-analyst",
            "status": "in_progress", "read_set": ["docs/architecture.md"],
            "write_set": ["src/cogem/graph.py"], "impact_set": ["README.md"],
            "core_impact_set": [], "depends_on": ["TASK-001"],
            "acceptance_checks": ["python -m unittest tests.test_graph -v"],
            "writing_lease": "lease-graph", "review_level": "standard"
        })
        decision = DecisionRecord.from_dict({
            "decision_id": "DEC-001", "title": "Provider-neutral models",
            "status": "accepted", "owner": "coordinator",
            "rationale": "Avoid model lock-in.", "affected_paths": ["agent-models.json"],
            "created_at": "2026-07-15T09:00:00+09:00"
        })
        handoff = HandoffRecord.from_dict({
            "handoff_id": "HANDOFF-001", "from_agent": "worker-a", "to_agent": "graph-analyst",
            "task_id": "TASK-002", "status": "pending", "summary": "Schema is ready.",
            "artifacts": ["skills/cogem/schemas/task.schema.json"],
            "verification": ["JSON parses"], "created_at": "2026-07-15T09:10:00+09:00"
        })
        message = AgentMessage.from_dict({
            "message_id": "MSG-001", "agent_id": "graph-analyst", "task_id": "TASK-002",
            "kind": "progress", "body": "Graph node scanning implemented.",
            "created_at": "2026-07-15T09:20:00+09:00"
        })
        state = CogemState(tasks={task.task_id: task}, decisions={decision.decision_id: decision},
                           handoffs={handoff.handoff_id: handoff}, messages=(message,), reports=(),
                           goals={
                               "GOAL-001": GoalRecord.from_dict({
                                   "goal_id": "GOAL-001",
                                   "objective": "Ship Cogem through a persistent leader loop.",
                                   "status": "active",
                                   "iteration": 2,
                                   "criteria": [{
                                       "criterion_id": "CRIT-001",
                                       "description": "The goal loop is verified.",
                                       "status": "pending",
                                       "evidence": [],
                                   }],
                                   "task_ids": ["TASK-002"],
                                   "current_gaps": ["Final review is pending."],
                                   "review_tree_hash": None,
                                   "blocker": None,
                                   "created_at": "2026-07-15T08:00:00+09:00",
                                   "updated_at": "2026-07-15T09:20:00+09:00",
                               })
                           })
        first = render_comm(
            state,
            objective="Ship Cogem",
            phase="implementation",
            graph_summary={"nodes": 12, "edges": 9},
            goal_actions={"GOAL-001": "repair"},
        )
        second = render_comm(
            state,
            objective="Ship Cogem",
            phase="implementation",
            graph_summary={"nodes": 12, "edges": 9},
            goal_actions={"GOAL-001": "repair"},
        )
        self.assertEqual(first, second)
        for heading in ("## Current Objective", "## Active Tasks", "## File and Section Ownership",
                        "## Shared Decisions", "## Pending Handoffs", "## Graphify Summary",
                        "## Active Goals", "## Goal Loop", "## Recent Agent Messages", "## Operator Notes"):
            self.assertIn(heading, first)
        self.assertIn("TASK-002", first)
        self.assertIn("GOAL-001", first)
        self.assertIn("repair", first)
        self.assertIn("Final review is pending.", first)
        self.assertIn("src/cogem/graph.py", first)

    def test_write_comm_preserves_only_operator_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Comm.md"
            path.write_text(
                "obsolete\n<!-- COGEM:OPERATOR_NOTES:START -->\nKeep this note.\n<!-- COGEM:OPERATOR_NOTES:END -->\n",
                encoding="utf-8",
            )
            write_comm(path, CogemState.empty(), objective="Objective", phase="ready")
            rendered = path.read_text(encoding="utf-8")
            self.assertIn("Keep this note.", rendered)
            self.assertNotIn("obsolete", rendered)


if __name__ == "__main__":
    unittest.main()
