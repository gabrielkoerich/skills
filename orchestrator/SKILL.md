---
name: orchestrator
description: Thin operational wrapper for a system-wide orchestrator CLI. Use when running and checking `orchestrator <command>` workflows without duplicating orchestration logic in the skill.
---

# Orchestrator (Thin Wrapper)

This skill intentionally stays minimal.

## Design

- Orchestrator is expected to be installed system-wide and available as `orchestrator`.
- This skill does **not** implement its own GitHub sync logic.
- This skill does **not** edit GitHub directly.
- It simply runs orchestrator commands consistently from scripts.

## Requirements

- `orchestrator` available on PATH
- `gh` auth/config handled by orchestrator itself

## Commands

| Script | Purpose |
|---|---|
| `scripts/reconcile.sh` | Run `orchestrator gh-sync` (or any `orchestrator <command>`)
| `scripts/check-drift.sh` | Quick health check via `orchestrator status` and optional command passthrough |

## Usage

```bash
# Default sync
orchestrator/scripts/reconcile.sh

# Explicit command
orchestrator/scripts/reconcile.sh gh-sync
orchestrator/scripts/reconcile.sh poll
orchestrator/scripts/reconcile.sh rejoin

# Health check
orchestrator/scripts/check-drift.sh

# Health + custom command
orchestrator/scripts/check-drift.sh tree
```

## Notes

- Keep all source-of-truth and GitHub mapping rules inside orchestrator itself.
- As orchestrator evolves, this skill should only mirror the CLI surface, not duplicate behavior.
