# Cogem Graph Model

The project graph represents directories, files, Markdown links, configured JSON path references, roles, tasks, decisions, handoffs, declared scope, impacts, and dependency order.

Each file node records size and a short content hash. The graph root is always `.` for portability.

## Input fingerprint

`project-graph.json` also records `input_fingerprint`, a full SHA-256 value over non-volatile graph inputs. It includes source and task/decision/handoff contracts while excluding `.graph/`, `Comm.md`, messages, reports, and scope snapshots.

`cogem dispatch-check` recomputes the fingerprint and blocks dispatch when it differs from the stored value.

## Outputs

```text
.graph/project-graph.json
.graph/project-graph.mmd
.graph/project-graph.md
.graph/parallel-safety-report.json
```

`.graph/` is generated for the target repository and is intentionally excluded from the portable release archive.
