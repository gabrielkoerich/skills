---
name: github-issue-worktree
description: Manage Git worktrees for isolated development environments per GitHub issue. Use `gh issue develop` to register linked branches and `git worktree` for isolated directories. Use it when the user explicity ask to work in a given github issue.
---

# Git Issue Worktree Workflow Skill

This skill defines a standardized workflow for managing tasks using Git worktrees, enabling isolated development environments for each issue while maintaining a clean main workspace.

---

## Requirements

- `gh` (GitHub CLI) installed and available on `PATH`
- `gh auth login` completed for the correct GitHub host/account
- Authenticated account has permission to read/write issues and pull requests in the target repository
- Git remote (`origin`) points to the repository where issues and PRs are managed

Quick verification:

```bash
gh auth status
gh repo view
gh issue list --limit 1
```

---

## What is Git Worktree?

Git worktree allows you to have multiple working directories attached to the same repository. Each worktree has its own checked-out branch, enabling you to work on different branches simultaneously without stashing or committing incomplete work.

### Benefits

- **Parallel Development**: Work on multiple branches simultaneously without switching
- **Clean Workspace**: Each task gets its own isolated directory
- **No Stashing**: No need to stash changes when switching contexts
- **Faster Context Switching**: Instantly jump between different tasks
- **Build Isolation**: Each worktree can have different build states

---

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
│     ├── Remove local worktree + local branch                   │
│     └── Prune stale worktree metadata                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Naming Conventions

Define names first and reuse them in all commands:

- `REPO_ROOT`: absolute repository root path from `git rev-parse --show-toplevel`
- `PROJECT_NAME`: directory name derived from `basename "$REPO_ROOT"`
- `WORKTREE_ROOT`: `~/.worktrees/<project-name>/`
- `BRANCH_NAME`: `gh-task-{issueId}-{shortTitle}`
- `shortTitle`: issue title slug (lowercase, spaces and special characters replaced with `-`)
- `WORKTREE_PATH`: `~/.worktrees/<project-name>/gh-task-{issueId}-{shortTitle}`

Compute these before creating any worktree:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
PROJECT_NAME="$(basename "$REPO_ROOT")"
WORKTREE_ROOT="$HOME/.worktrees/$PROJECT_NAME"
BRANCH_NAME="gh-task-{issueId}-{shortTitle}"
WORKTREE_PATH="$WORKTREE_ROOT/$BRANCH_NAME"
mkdir -p "$WORKTREE_ROOT"
```

## Step-by-Step Instructions

### 1. Start Work on a New Issue

#### 1.1 Comment on the Issue

Before starting, comment on the GitHub issue with your plan:

```bash
gh issue comment {issueId} --body "## 🚀 Starting Work

**Plan:**
1. Step 1 description
2. Step 2 description
3. Step 3 description

**Estimated Time:** X hours

**Worktree:** ~/.worktrees/<project-name>/gh-task-{issueId}-{shortTitle}"
```

#### 1.2 Register the Branch Link via GitHub CLI

```bash
# Make sure you are in the project directory and on the intended base branch.

# Branch naming format: gh-task-{issueId}-{shortTitle}
gh issue develop {issueId} \
  --base main \
  --name gh-task-{issueId}-{shortTitle}
```

#### 1.3 Create the Worktree from the Linked Branch

```bash
# Attach a separate working directory to the branch created above
git worktree add ~/.worktrees/<project-name>/gh-task-{issueId}-{shortTitle} gh-task-{issueId}-{shortTitle}

# Navigate to the new worktree
cd ~/.worktrees/<project-name>/gh-task-{issueId}-{shortTitle}
```

**What this does:**
- `gh issue develop` creates and links the branch in GitHub's Development graph
- `git worktree add` creates a separate local directory for that linked branch
- The new worktree shares the same `.git` object database (space efficient)

**Important:** Avoid `gh issue develop --checkout` when you plan to use worktrees. A branch can only be checked out in one worktree at a time.

---

### 2. Development Phase

#### 2.1 Work in the New Directory

All development happens in the new worktree directory:

```bash
# You're now in ~/.worktrees/<project-name>/gh-task-{issueId}-{shortTitle}
# Make your changes, edit files, create new ones
```

#### 2.2 Commit Changes

```bash
# Stage and commit as you work
git add .
git commit -m "feat: descriptive commit message"
```

#### 2.3 Push to Remote

```bash
# Push the branch to remote
git push -u origin gh-task-{issueId}-{shortTitle}
```

---

### 3. Submit Work

#### 3.1 Create Pull Request

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

#### 3.2 Link PR to Issue

Two options:
- Auto-close on merge: include `Closes #{issueId}` or `Fixes #{issueId}` in PR body
- Relation only (no auto-close): use `Related to #{issueId}` and link in GitHub UI sidebar if needed

#### 3.3 Comment on Issue

After PR is created, comment completion on the issue:

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

---

### 4. Cleanup (After PR Merge)

#### 4.1 Update Labels

```bash
# Remove in-progress label, add done label
gh issue edit {issueId} \
  --remove-label "status:in-progress" \
  --add-label "status:done"
```

#### 4.2 Remove Worktree and Local Branch

```bash
# Navigate back to main repository

# Remove the worktree (this also deletes the directory)
git worktree remove ~/.worktrees/<project-name>/gh-task-{issueId}-{shortTitle}

# Clean up local branch after merge
git branch -d gh-task-{issueId}-{shortTitle}
```

#### 4.3 Prune Metadata

```bash
git worktree prune
```

---

## Quick Reference Commands

### Worktree Management

```bash
# List all worktrees
git worktree list

# Create new worktree
git worktree add <path> [<branch>]

# Remove worktree
git worktree remove <path>

# Prune stale worktrees (removes tracking for deleted directories)
git worktree prune

# Lock a worktree (prevent automatic removal)
git worktree lock <path>

# Unlock a worktree
git worktree unlock <path>
```

### Branch from Specific Base

```bash
# Preferred: register linked branch first, then attach worktree
gh issue develop {id} --base main --name gh-task-{id}
git worktree add ~/.worktrees/<project-name>/gh-task-{id} gh-task-{id}
```

### Move Worktree

```bash
# Relocate a worktree
git worktree move <old-path> <new-path>
```

---

## Best Practices

### Naming Conventions

- **Worktree Directory**: `~/.worktrees/<project-name>/gh-task-{issueId}-{shortTitle}`
- **Branch Name**: `gh-task-{issueId}-{shortTitle}`
- Keep titles concise but descriptive (max 3-4 words)

### Worktree Root Strategy

Use a dedicated directory outside repositories to avoid status noise and accidental commits.

- Recommended: `~/.worktrees/<project-name>/`
- Alternative: `./worktrees/` if you want repo-local organization
- Required for project-local mode: keep `/worktrees/` in `.gitignore`

Compute the default worktree root from the current repository:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
PROJECT_NAME="$(basename "$REPO_ROOT")"
WORKTREE_ROOT="$HOME/.worktrees/$PROJECT_NAME"
mkdir -p "$WORKTREE_ROOT"
```

If you use a project-local root, ignore it in Git:

```bash
echo "/worktrees/" >> .gitignore
git add .gitignore
```

### Example

For issue #42 "Add user authentication":
- Directory: `~/.worktrees/my-repo/gh-task-42-add-user-auth`
- Branch: `gh-task-42-add-user-auth`

### Do's and Don'ts

| ✅ Do | ❌ Don't |
|-------|----------|
| Register linked branch, then create worktree | Work directly in main repo for isolated tasks |
| Use descriptive branch names | Use generic names like `fix`, `feature` |
| Commit regularly in the worktree | Wait until the end to commit |
| Clean up after PR merge | Leave orphaned worktrees |
| Run tests before pushing | Push untested code |
| Link PR to issue | Forget to reference the issue |
| Keep worktrees in a dedicated root directory | Mix worktrees into tracked project paths |
| Ensure local worktree root is gitignored | Commit worktree directories by accident |

---

## Troubleshooting

### Worktree Already Exists

```bash
# If you get "already checked out" error
git worktree list  # Check existing worktrees
git worktree remove <path>  # Remove if stale
```

### Permission Errors

```bash
# If worktree removal fails due to permissions
# Manually delete directory, then:
git worktree prune
```

### Branch Already Exists

```bash
# Create worktree from existing branch
git worktree add ~/.worktrees/<project-name>/gh-task-{id} gh-task-{id}

# Optionally register the existing branch to an issue
gh issue develop {id} --name gh-task-{id}
```

---

## Template: Complete Workflow Script

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
REPO_ROOT=$(git rev-parse --show-toplevel)
REPO_NAME=$(basename "$REPO_ROOT")
WORKTREE_ROOT="${WORKTREE_ROOT:-$HOME/.worktrees/$REPO_NAME}"
WORKTREE_PATH="$WORKTREE_ROOT/$BRANCH_NAME"

mkdir -p "$WORKTREE_ROOT"

# If using project-local worktrees, ensure they are ignored by git
case "$WORKTREE_ROOT/" in
  "$REPO_ROOT"/*)
    IGNORE_REL="/${WORKTREE_ROOT#$REPO_ROOT/}/"
    touch "$REPO_ROOT/.gitignore"
    if ! grep -Fxq "$IGNORE_REL" "$REPO_ROOT/.gitignore"; then
      echo "$IGNORE_REL" >> "$REPO_ROOT/.gitignore"
      echo "📝 Added $IGNORE_REL to .gitignore"
    fi
    ;;
esac

# Idempotency: if branch is already checked out in another worktree, reuse that path
EXISTING_BRANCH_PATH=$(git worktree list --porcelain \
  | awk -v b="refs/heads/$BRANCH_NAME" '
      $1=="worktree"{wt=$2}
      $1=="branch" && $2==b{print wt; exit}
    ')

if [ -n "$EXISTING_BRANCH_PATH" ]; then
  echo "ℹ️ Branch $BRANCH_NAME is already checked out at:"
  echo "   $EXISTING_BRANCH_PATH"
  echo "   Reuse it with: cd $EXISTING_BRANCH_PATH"
  exit 0
fi

# Prevent path collisions by adding numeric suffix if needed
if [ -e "$WORKTREE_PATH" ]; then
  i=2
  while [ -e "${WORKTREE_PATH}-$i" ]; do
    i=$((i + 1))
  done
  WORKTREE_PATH="${WORKTREE_PATH}-$i"
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
git worktree add "$WORKTREE_PATH" "$BRANCH_NAME"

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

---

## Related Documentation

- [Git Worktree Documentation](https://git-scm.com/docs/git-worktree)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

## Workflow Checklist

Use this checklist for each task:

- [ ] Comment on issue with "## 🚀 Starting Work" and plan
- [ ] Register branch link: `gh issue develop {id} --base main --name gh-task-{id}-{title}`
- [ ] Create worktree: `git worktree add ~/.worktrees/<project-name>/gh-task-{id}-{title} gh-task-{id}-{title}`
- [ ] Implement solution in worktree
- [ ] Commit changes with descriptive messages
- [ ] Push branch to remote
- [ ] Create PR from branch to main
- [ ] Ensure PR description includes `Closes #{issueId}` (auto-close) or `Related to #{issueId}` (relation only)
- [ ] Comment "## ✅ Task Completed" on issue
- [ ] Update labels: remove `status:in-progress`, add `status:done`
- [ ] Remove worktree and local branch after merge
- [ ] Prune metadata: `git worktree prune`
