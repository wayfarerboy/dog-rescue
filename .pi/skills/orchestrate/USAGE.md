# /orchestrate

Autonomous issue orchestration for this repo.

## Quick start

1. Label an issue `ready-for-agent`
2. Run `/orchestrate` from the `dev` branch
3. The orchestrator fetches `ready-for-agent` issues, plans them, and dispatches up to 4 parallel issue-handler agents
4. Each handler implements the issue with TDD (`pytest`), runs linting (`ruff`), self-reviews, and commits
5. Completed branches are merged back into `dev`, labels are updated, and `dev` is pushed

## Prerequisites

- GitHub CLI (`gh`) authenticated
- Python 3.10+, `ruff`, `pytest`, `requests`, `beautifulsoup4` installed
- Issues must have the `ready-for-agent` label

## Branch strategy

```
main ← (manual merge from dev) ← dev ← agent/dev/issue-1, agent/dev/issue-2, ...
```

The orchestrator works on `dev`. Manual PR from `dev` → `main` is up to you.

## Label workflow

| Label | Meaning |
|---|---|
| `ready-for-agent` | Fully specified, ready for autonomous implementation |
| `reviewed` | Handler completed; awaiting human review (if `reviewLabel` configured) |

## Settings

See `.pi/settings.json` for concurrency, model overrides, and the `orchestrate.reviewLabel`.
