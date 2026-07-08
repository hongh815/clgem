# hongh-skills — Claude Code Plugin Marketplace

Personal Claude Code skill marketplace.

## Plugins

- **clgem** — Leader Claude (Fable 5) multi-agent orchestration: the leader does
  architecture, planning, verification, and task allocation; worker agents run on
  cost-optimized models (sonnet/haiku); a separate Codex CLI (`codex`) session
  critically reviews every completed task; all coordination is logged in Comm.md;
  work iterates against a /goal until acceptance criteria are met.

## Install on any machine

```
/plugin marketplace add <github-username>/claude-skills
/plugin install clgem@hongh-skills
```

## Update

```
/plugin marketplace update hongh-skills
```
