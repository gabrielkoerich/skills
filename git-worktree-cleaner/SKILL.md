---
name: git-worktree-cleaner
description: Audit and clean git worktrees safely across repositories, including stale metadata and merged local branches.
---

# Worktree Cleaner

Use this skill to inspect, clean, and prune worktrees safely after a PR has been merged.

## Commands

```bash
# List all worktrees in current repo
git worktree list

# Audit: show stale entries and merged branches (dry-run)
git worktree list
git branch --merged | sed 's/^..//'

# Remove a specific worktree
git worktree remove <path>

# Delete a merged local branch
git branch -d <branch-name>

# Prune stale worktree metadata (tracking for deleted directories)
git worktree prune
```

## Workflow

1. **Audit first** — always list worktrees and merged branches before removing anything
2. **Remove worktree** — `git worktree remove <path>` deletes the directory and unregisters it
3. **Delete local branch** — `git branch -d <branch>` only works if the branch is merged (safe)
4. **Prune metadata** — `git worktree prune` cleans up references to worktrees whose directories no longer exist

## Guardrails

- Never remove the current worktree.
- Always audit before removing — list worktrees and check which branches are merged.
- Only delete local branches proven merged (`git branch -d`, not `-D`).
- Do not force-delete unmerged branches unless explicitly asked.
