# Graphify-Aware Skill Authoring and Cross-Reviewer Design

## Goal

Make skills produced or updated through clgem use Graphify as evidence for cross-file
connectivity, and add Antigravity CLI as an optional, independent critical reviewer.

## Graphify-aware skill authoring

When a task creates or changes a skill, the Leader maps the entire designated path when
it contains more than one relevant resource. The graph is used to find related skill
instructions, templates, references, and scripts before editing. After changes, the
Leader refreshes the graph and checks for unexpected isolation, lost expected links, or
other connectivity regressions. Extracted edges are evidence; inferred and ambiguous
edges remain hypotheses to verify.

## Review architecture

Codex remains the default, mandatory reviewer. Antigravity CLI (`agy`) is an optional
second reviewer, used for high-risk or ambiguous work, explicit user requests, and
Graphify-derived regression signals. It receives an independent prompt containing the
goal, task, artifacts, active directives, and graph evidence; it does not receive
Codex's verdict before forming its own judgment.

The Antigravity process runs non-interactively through `agy -p`, requests sandboxed
execution, writes a persisted output file, and returns the same `VERDICT`/`FINDINGS`
contract as Codex. A missing CLI, failed response, or unusable verdict is recorded as
a skipped secondary check and never substitutes for the default Codex gate.

## Resolving disagreement

When Codex and Antigravity disagree, the Leader compares cited evidence rather than
voting. A material unsupported claim can trigger one targeted follow-up with the
reviewer that made it. The Leader records both verdicts, the evidence considered, and
the resulting ACCEPT, SUPPLEMENT, or REDO decision.

## Verification

Validate all changed Markdown references, confirm `agy --version` and `agy --help`
expose non-interactive and sandbox options, and run a harmless `agy -p` capability
probe only after the user has authorized the implementation.
