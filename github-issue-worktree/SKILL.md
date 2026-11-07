---
name: github-issue-worktree
description: Manage an isolated worktree per GitHub issue. Register the branch with `gh issue develop`, then create, list, and remove the worktree with `git cow` only, by following the git-worktrees skill. The default directory is `~/.worktrees/<project>/`. Use it when the user explicitly asks to work on a GitHub issue.
---

# Git Issue Worktree Workflow Skill

This skill covers the issue workflow. The git-worktrees skill owns the worktree. Read that skill and follow it. Call `git cow` only. A new worktree goes in `~/.worktrees/<project>/`. If `git cow list` already has the branch under `<project>/.claude/worktrees`, use that path.

## Requirements

- `gh` (GitHub CLI) is installed and on `PATH`
- `gh auth login` is done for the correct GitHub host/account
- The authenticated account can read and write issues and pull requests in the target repository
- The Git remote (`origin`) points to the repository that holds the issues and PRs

Check:

```bash
gh auth status
gh repo view
gh issue list --limit 1
```

## What is Git Worktree?

A worktree is an extra working directory attached to the same repository. Each worktree has its own checked-out branch, so you can work on several branches at once without stashing or committing unfinished work.

### Benefits

- Work on several branches at once without switching
- Each task gets its own isolated directory
- No stash when you switch tasks
- Switch between tasks instantly
- Each worktree keeps its own build state

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    GIT WORKTREE WORKFLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. START WORK                                                  │
│     ├── Comment on issue: "## 🚀 Starting Work" + plan          │
│     ├── Register branch link: gh issue develop {id}            │
│     ├── Create worktree from linked branch                      │
│     └── Work in new directory                                   │
│                                                                 │
│  2. DEVELOPMENT                                                 │
│     ├── Implement solution in worktree                          │
│     ├── Commit changes                                          │
│     └── Push to remote branch                                   │
│                                                                 │
│  3. SUBMIT WORK                                                 │
│     ├── Create Pull Request (from feature → main)               │
│     ├── Link PR to issue                                        │
│     └── Comment: "## ✅ Task Completed" + summary               │
│                                                                 │
│  4. CLEANUP (after merge)                                       │
│     ├── Update labels: status:in-progress → status:done         │
│     └── git cow remove --warm, from the main checkout          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Naming conventions

Set these names first and use them in all commands:

- `PROJECT_NAME`: directory name of the main checkout
- `WORKTREE_ROOT`: `~/.worktrees/<project-name>/`
- `BRANCH_NAME`: `gh-task-{issueId}-{shortTitle}`
- `shortTitle`: issue title slug (lowercase, spaces and special characters replaced with `-`)
- `WORKTREE_PATH`: `~/.worktrees/<project-name>/gh-task-{issueId}-{shortTitle}`

Compute them before you create a worktree. This works when the current directory is already a worktree:

```bash
common=$(git rev-parse --path-format=absolute --git-common-dir)
PROJECT_NAME=$(basename "$(dirname "$common")")
WORKTREE_ROOT="$HOME/.worktrees/$PROJECT_NAME"
BRANCH_NAME="gh-task-{issueId}-{shortTitle}"
WORKTREE_PATH="$WORKTREE_ROOT/$BRANCH_NAME"
```

## Steps

### 1. Start work on a new issue

#### 1.1 Comment on the issue

Before you start, post your plan as a comment on the issue:

```bash
gh issue comment {issueId} --body "## 🚀 Starting Work

**Plan:**
1. Step 1 description
2. Step 2 description
3. Step 3 description

**Estimated Time:** X hours

**Worktree:** ~/.worktrees/<project-name>/gh-task-{issueId}-{shortTitle}"
```

#### 1.2 Register the branch link with the GitHub CLI

```bash
# Make sure you are in the project directory and on the intended base branch.

# Branch naming format: gh-task-{issueId}-{shortTitle}
gh issue develop {issueId} \
  --base main \
  --name gh-task-{issueId}-{shortTitle}
```

#### 1.3 Create the worktree from the linked branch

```bash
git cow add ~/.worktrees/<project-name>/gh-task-{issueId}-{shortTitle} gh-task-{issueId}-{shortTitle}
cd ~/.worktrees/<project-name>/gh-task-{issueId}-{shortTitle}
```

The branch already exists, so the path comes first. Follow the git-worktrees skill for that command.

Do not use `gh issue develop --checkout` with worktrees. Git checks out a branch in only one worktree at a time.

### 2. Development

#### 2.1 Work in the new directory

Do all development in the new worktree directory:

```bash
# You're now in ~/.worktrees/<project-name>/gh-task-{issueId}-{shortTitle}
# Make your changes, edit files, create new ones
```

#### 2.2 Commit changes

```bash
# Stage and commit as you work
git add .
git commit -m "feat: descriptive commit message"
```

#### 2.3 Push to remote

```bash
# Push the branch to remote
git push -u origin gh-task-{issueId}-{shortTitle}
```

### 3. Submit work

#### 3.1 Create the pull request

```bash
# Create PR from current branch to main
gh pr create \
  --base main \
  --head gh-task-{issueId}-{shortTitle} \
  --title "feat: {descriptive title referencing shortTitle}" \
  --body "## Summary

Brief description of changes.

## Changes

- Change 1
- Change 2
- Change 3

## Related

Closes #{issueId}"
```

#### 3.2 Link the PR to the issue

Two options:
- Close the issue on merge: put `Closes #{issueId}` or `Fixes #{issueId}` in the PR body
- Relation only, no auto-close: use `Related to #{issueId}`, and link it in the GitHub UI sidebar if needed

#### 3.3 Comment on the issue

After you create the PR, post a completion comment on the issue:

```bash
gh issue comment {issueId} --body "## ✅ Task Completed

**Summary:**
Brief description of what was done.

**Pull Request:** {pr-url}

**Changes:**
- Change 1
- Change 2
- Change 3"
```

### 4. Cleanup (after the PR merges)

#### 4.1 Update labels

```bash
# Remove in-progress label, add done label
gh issue edit {issueId} \
  --remove-label "status:in-progress" \
  --add-label "status:done"
```

#### 4.2 Remove the worktree and local branch

From the main checkout, follow the git-worktrees skill:

```bash
git cow remove --warm ~/.worktrees/<project-name>/gh-task-{issueId}-{shortTitle}
```

This removes the worktree. It also deletes the branch if the branch is merged.

## Quick reference

### Worktree management

```bash
git cow list
git cow add ~/.worktrees/<project-name>/gh-task-{id} gh-task-{id}
git cow remove --warm ~/.worktrees/<project-name>/gh-task-{id}
```

### Branch from a specific base

```bash
gh issue develop {id} --base main --name gh-task-{id}
git cow add ~/.worktrees/<project-name>/gh-task-{id} gh-task-{id}
```

## Best practices

### Names

- Worktree directory: `~/.worktrees/<project-name>/gh-task-{issueId}-{shortTitle}`
- Branch name: `gh-task-{issueId}-{shortTitle}`
- Keep titles short and descriptive (3-4 words at most)

### Worktree root

The default directory is `~/.worktrees/<project-name>/`. Follow the git-worktrees skill for the path. An existing Claude Code worktree under `<project>/.claude/worktrees` stays there.

```bash
common=$(git rev-parse --path-format=absolute --git-common-dir)
PROJECT_NAME=$(basename "$(dirname "$common")")
WORKTREE_ROOT="$HOME/.worktrees/$PROJECT_NAME"
```

### Example

For issue #42 "Add user authentication":
- Directory: `~/.worktrees/my-repo/gh-task-42-add-user-auth`
- Branch: `gh-task-42-add-user-auth`

### Do and don't

| Do | Don't |
|-------|----------|
| Register linked branch, then create worktree | Work directly in main repo for isolated tasks |
| Use descriptive branch names | Use generic names like `fix`, `feature` |
| Commit regularly in the worktree | Wait until the end to commit |
| Clean up after PR merge | Leave orphaned worktrees |
| Run tests before pushing | Push untested code |
| Link PR to issue | Forget to reference the issue |
| Keep worktrees in a dedicated root directory | Mix worktrees into tracked project paths |
| Ensure local worktree root is gitignored | Commit worktree directories by accident |

## Troubleshooting

### Worktree already exists

```bash
git cow list
```

Reuse the path it prints for that branch.

### Branch already exists

```bash
git cow add ~/.worktrees/<project-name>/gh-task-{id} gh-task-{id}
gh issue develop {id} --name gh-task-{id}
```

## Template: complete workflow script

```bash
#!/bin/bash
# Complete workflow automation template

set -euo pipefail

ISSUE_ID="${1:-}"
if [ -z "$ISSUE_ID" ]; then
  echo "Usage: $0 <issue-id>"
  exit 1
fi

# Pull issue title and sanitize into slug (lowercase, a-z0-9- only)
ISSUE_TITLE=$(gh issue view "$ISSUE_ID" --json title -q .title)
BRANCH_SLUG=$(echo "$ISSUE_TITLE" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-{2,}/-/g' \
  | cut -c1-30)
BRANCH_NAME="gh-task-${ISSUE_ID}-${BRANCH_SLUG}"

# Configurable defaults
BASE_BRANCH="${BASE_BRANCH:-main}"
common=$(git rev-parse --path-format=absolute --git-common-dir)
REPO_NAME=$(basename "$(dirname "$common")")
WORKTREE_ROOT="${WORKTREE_ROOT:-$HOME/.worktrees/$REPO_NAME}"
WORKTREE_PATH="$WORKTREE_ROOT/$BRANCH_NAME"

# If the branch is already checked out, reuse that path
EXISTING_BRANCH_PATH=$(git cow list | awk -F '\t' -v b="$BRANCH_NAME" '$2==b {print $1; exit}')

if [ -n "$EXISTING_BRANCH_PATH" ]; then
  echo "ℹ️ Branch $BRANCH_NAME is already checked out at:"
  echo "   $EXISTING_BRANCH_PATH"
  echo "   Reuse it with: cd $EXISTING_BRANCH_PATH"
  exit 0
fi

if [ -e "$WORKTREE_PATH" ]; then
  echo "Path already exists: $WORKTREE_PATH"
  exit 1
fi

# 1. Comment on issue
echo "📋 Commenting on issue #${ISSUE_ID}..."
gh issue comment "$ISSUE_ID" --body "## 🚀 Starting Work

**Plan:**
1. Analyze requirements
2. Implement solution
3. Test and verify
4. Create PR

**Worktree:** ${WORKTREE_PATH}"

# 2. Register linked branch in GitHub
echo "🔗 Registering branch link..."
gh issue develop "$ISSUE_ID" --base "$BASE_BRANCH" --name "$BRANCH_NAME"

# Optional verification that GitHub recognizes branch linkage
echo "🔍 Verifying linked branches..."
gh issue develop --list "$ISSUE_ID"

# 3. Create local worktree from linked branch
echo "🔧 Creating worktree..."
git cow add "$WORKTREE_PATH" "$BRANCH_NAME"

echo "✅ Worktree created at: $WORKTREE_PATH"
echo "📁 Navigate with: cd $WORKTREE_PATH"
echo ""
echo "Next steps:"
echo "  1. cd $WORKTREE_PATH"
echo "  2. Make your changes"
echo "  3. git add . && git commit -m \"feat: ...\""
echo "  4. git push -u origin $BRANCH_NAME"
echo "  5. gh pr create --base $BASE_BRANCH --fill"
echo "  6. Use 'Related to #${ISSUE_ID}' (relation only) or 'Closes #${ISSUE_ID}' (auto-close)"
```

## Related documentation

- the git-worktrees skill
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## Workflow checklist

Use this checklist for each task:

- [ ] Comment on issue with "## 🚀 Starting Work" and plan
- [ ] Register branch link: `gh issue develop {id} --base main --name gh-task-{id}-{title}`
- [ ] Create worktree: `git cow add ~/.worktrees/<project-name>/gh-task-{id}-{title} gh-task-{id}-{title}`
- [ ] Implement solution in worktree
- [ ] Commit changes with descriptive messages
- [ ] Push branch to remote
- [ ] Create PR from branch to main
- [ ] Make sure the PR description includes `Closes #{issueId}` (auto-close) or `Related to #{issueId}` (relation only)
- [ ] Comment "## ✅ Task Completed" on issue
- [ ] Update labels: remove `status:in-progress`, add `status:done`
- [ ] From the main checkout, `git cow remove --warm` on the worktree path
