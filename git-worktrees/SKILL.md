---
name: git-worktrees
description: Manage plain Git worktree feature branches without issue linking. Create a feature branch worktree, develop in isolation, push, and open a PR with commit-based changes summary.
---

# Git Worktrees Skill

Use this workflow when you want isolated feature development with Git worktrees only.
Do not use GitHub issue linking commands in this skill.

## Requirements

- Git installed and repository has `origin` configured
- `gh` installed, authenticated, and authorized for PR creation

Quick verification:

```bash
git remote -v
gh auth status
gh repo view
```

## Input Rules

- If the user explicitly provides a feature name, use it.
- If the request clearly implies a single feature name, derive one and proceed.
- If the request is ambiguous, ask one direct question: `What feature name should I use for the branch/worktree?`

## Naming Conventions

Define names first and reuse them in all commands:

- `REPO_ROOT`: absolute repository root path from `git rev-parse --show-toplevel`
- `PROJECT_NAME`: directory name derived from `basename "$REPO_ROOT"`
- `FEATURE_NAME`: user-facing feature label
- `featureSlug`: lowercase slug from `FEATURE_NAME` (spaces/special chars replaced with `-`)
- `BRANCH_NAME`: `feat/{featureSlug}`
- `WORKTREE_ROOT`: `~/.worktrees/<project-name>/`
- `WORKTREE_PATH`: `~/.worktrees/<project-name>/{featureSlug}`

Compute before creating the worktree:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
PROJECT_NAME="$(basename "$REPO_ROOT")"
FEATURE_NAME="add login page"
featureSlug=$(echo "$FEATURE_NAME" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-{2,}/-/g' \
  | cut -c1-40)
BRANCH_NAME="feat/$featureSlug"
WORKTREE_ROOT="$HOME/.worktrees/$PROJECT_NAME"
WORKTREE_PATH="$WORKTREE_ROOT/$featureSlug"
mkdir -p "$WORKTREE_ROOT"
```

## Workflow

1. Create a feature branch + worktree
2. Develop in the worktree
3. Commit and push
4. Create a PR with changes summary
5. Clean up after merge

## 1) Start a Feature Worktree

```bash
BASE_BRANCH="${BASE_BRANCH:-main}"

# If branch already checked out in another worktree, reuse it
EXISTING_BRANCH_PATH=$(git worktree list --porcelain \
  | awk -v b="refs/heads/$BRANCH_NAME" '
      $1=="worktree"{wt=$2}
      $1=="branch" && $2==b{print wt; exit}
    ')

if [ -n "$EXISTING_BRANCH_PATH" ]; then
  echo "Branch already checked out at: $EXISTING_BRANCH_PATH"
  cd "$EXISTING_BRANCH_PATH"
else
  # Avoid path collisions
  if [ -e "$WORKTREE_PATH" ]; then
    i=2
    while [ -e "${WORKTREE_PATH}-$i" ]; do
      i=$((i + 1))
    done
    WORKTREE_PATH="${WORKTREE_PATH}-$i"
  fi

  git fetch origin "$BASE_BRANCH"
  git worktree add -b "$BRANCH_NAME" "$WORKTREE_PATH" "origin/$BASE_BRANCH"
  cd "$WORKTREE_PATH"
fi
```

## 2) Develop

```bash
# edit files, run tests, etc.
git status
```

## 3) Commit and Push

```bash
git add -A
git commit -m "feat: implement $featureSlug"
git push -u origin "$BRANCH_NAME"
```

## 4) Create PR with Changes Summary

Use commit subjects between `origin/<base>` and `HEAD` as PR summary bullets.

```bash
BASE_BRANCH="${BASE_BRANCH:-main}"

PR_BODY=$(cat <<PR
## Summary

$(git log --no-merges --pretty='- %s' "origin/$BASE_BRANCH..HEAD")

## Testing

- [ ] Add testing notes
PR
)

gh pr create \
  --base "$BASE_BRANCH" \
  --head "$BRANCH_NAME" \
  --title "feat: $featureSlug" \
  --body "$PR_BODY"
```

## 5) Cleanup (After Merge)

```bash
# from primary repo
git worktree remove "$WORKTREE_PATH"
git branch -d "$BRANCH_NAME"
git worktree prune
```

## Quick Commands

```bash
git worktree list
git worktree remove <path>
git worktree prune
```

## Guardrails

- One branch can only be checked out in one worktree at a time.
- Keep feature names short and descriptive.
- Prefer `~/.worktrees/<project-name>/` as the default worktree root.
- If you choose repo-local worktrees, ensure they are ignored in `.gitignore`.
