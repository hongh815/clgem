# Cogem Parallel Safety Reference

A pair is safe only when no reason code is emitted.

| Reason code | Trigger |
| --- | --- |
| `SAME_TASK` | A task is compared with itself |
| `MISSING_SCOPE` | A source-writing task has no writes |
| `WRITE_WRITE_CONFLICT` | Write sets overlap |
| `WRITE_READ_CONFLICT` | One task writes an input read by the other |
| `DEPENDENCY_CONFLICT` | Direct or transitive dependency exists |
| `CORE_IMPACT_CONFLICT` | Core impact sets overlap |
| `LEASE_CONFLICT` | Tasks share a writing lease |

Unknown scope is unsafe. Distinct files are insufficient when one task changes a contract consumed by the other. The Coordinator either serializes the tasks, merges them, or redesigns their boundaries and reruns the check.
