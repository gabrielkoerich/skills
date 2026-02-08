---
name: skill-creator
description: Create or update repository-local skills with consistent SKILL.md structure, scripts, and agents/openai.yaml metadata.
---

# Skill Creator (Local)

Use this skill to scaffold new skills in this repository with consistent structure.

## Workflow

1. Create `<skill-name>/SKILL.md`
2. Add optional `scripts/` for deterministic tasks
3. Add `agents/openai.yaml`
4. Run `skill-lint`

## Scaffold Command

```bash
scripts/init-skill.sh <skill-name> "<description>"
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
