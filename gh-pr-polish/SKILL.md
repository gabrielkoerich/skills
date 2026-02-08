---
name: gh-pr-polish
description: Generate high-signal PR titles and bodies from git history and changed files, then open PRs with gh CLI.
---

# GH PR Polish

Use this skill to produce consistent PR descriptions and open PRs with `gh`.

## Requirements

- `gh` installed and authenticated
- working branch pushed to `origin`

## Commands

```bash
# Generate title/body from current branch vs base
scripts/make-pr-body.sh main

# Create PR with generated content
scripts/create-pr.sh main
```

## Publishing Patterns

### Claude Code

```bash
cp -r <skill-dir> ~/.claude/skills/<skill-name>
```

### OpenCode

```bash
cp -r <skill-dir> <workspace>/skills/<skill-name>
```
