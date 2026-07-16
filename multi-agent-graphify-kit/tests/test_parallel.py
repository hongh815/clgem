import unittest

from cogem.contracts import TaskRecord
from cogem.parallel import assess_parallel_safety


def task(task_id, *, reads=(), writes=(), impacts=(), core=(), deps=(), lease=None):
    return TaskRecord.from_dict({
        "task_id": task_id,
        "title": task_id,
        "owner": task_id.lower(),
        "status": "ready",
        "read_set": list(reads),
        "write_set": list(writes),
        "impact_set": list(impacts),
        "core_impact_set": list(core),
        "depends_on": list(deps),
        "acceptance_checks": [],
        "writing_lease": lease or f"lease-{task_id.lower()}",
        "review_level": "standard"
    })


class ParallelSafetyTests(unittest.TestCase):
    def test_independent_tasks_are_safe(self):
        a = task("TASK-001", writes=("a.md",), reads=("shared.md",))
        b = task("TASK-002", writes=("b.md",), reads=("shared.md",))
        result = assess_parallel_safety(a, b, {a.task_id: a, b.task_id: b})
        self.assertTrue(result.parallel_safe)
        self.assertEqual(result.reason_codes, ())

    def test_write_write_conflict_is_unsafe(self):
        a = task("TASK-001", writes=("same.md",))
        b = task("TASK-002", writes=("same.md",))
        result = assess_parallel_safety(a, b, {a.task_id: a, b.task_id: b})
        self.assertFalse(result.parallel_safe)
        self.assertIn("WRITE_WRITE_CONFLICT", result.reason_codes)

    def test_write_read_conflict_is_unsafe(self):
        a = task("TASK-001", writes=("schema.json",))
        b = task("TASK-002", reads=("schema.json",), writes=("docs.md",))
        result = assess_parallel_safety(a, b, {a.task_id: a, b.task_id: b})
        self.assertIn("WRITE_READ_CONFLICT", result.reason_codes)

    def test_transitive_dependency_is_unsafe(self):
        a = task("TASK-001", writes=("a.md",))
        mid = task("TASK-002", writes=("b.md",), deps=("TASK-001",))
        b = task("TASK-003", writes=("c.md",), deps=("TASK-002",))
        tasks = {x.task_id: x for x in (a, mid, b)}
        result = assess_parallel_safety(a, b, tasks)
        self.assertIn("DEPENDENCY_CONFLICT", result.reason_codes)

    def test_shared_core_impact_is_unsafe(self):
        a = task("TASK-001", writes=("a.md",), core=("AGENTS.md",))
        b = task("TASK-002", writes=("b.md",), core=("AGENTS.md",))
        result = assess_parallel_safety(a, b, {a.task_id: a, b.task_id: b})
        self.assertIn("CORE_IMPACT_CONFLICT", result.reason_codes)

    def test_missing_scope_is_unsafe(self):
        a = task("TASK-001")
        b = task("TASK-002", writes=("b.md",))
        result = assess_parallel_safety(a, b, {a.task_id: a, b.task_id: b})
        self.assertIn("MISSING_SCOPE", result.reason_codes)


if __name__ == "__main__":
    unittest.main()
