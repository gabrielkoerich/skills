---
name: worktree-janitor
description: Audit and clean git worktrees safely across repositories, including stale metadata and merged local branches.
---

# Worktree Janitor

Use this skill to inspect, clean, and prune worktrees safely.

## Commands

```bash
# List worktrees in current repo
scripts/janitor.sh list

# Show stale entries and merged branches (dry-run)
scripts/janitor.sh audit

# Remove a specific worktree path
scripts/janitor.sh remove <path>

# Prune stale metadata
scripts/janitor.sh prune
```

## Guardrails

- Never remove the current worktree.
- Default to dry-run style audit first.
- Only delete local branches proven merged.

## Publishing Patterns

### Claude Code

```bash
cp -r <skill-dir> ~/.claude/skills/<skill-name>
```

### OpenCode

```bash
cp -r <skill-dir> <workspace>/skills/<skill-name>
```
