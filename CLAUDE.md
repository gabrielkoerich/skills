# CLAUDE.md

This is a **skill library** and **Claude Code plugin marketplace** — a collection of independent, self-contained skills for AI agents. Each skill lives in its own directory with a `SKILL.md` documentation file.

## Skill Structure

```
skill-name/
├── SKILL.md                    # Documentation and frontmatter (required)
├── .claude-plugin/plugin.json  # Plugin metadata (auto-generated)
├── agents/openai.yaml          # OpenAI/Codex agent config (auto-generated)
├── scripts/                    # Executable scripts (bash/python)
└── src/                        # Source code (TypeScript projects)
```

Each `SKILL.md` has YAML frontmatter with `name` and `description`. These are the single source of truth — the workflow auto-generates `plugin.json`, `agents/openai.yaml`, the README table, and `.claude-plugin/marketplace.json` from them.

## Automation

`python .github/workflows/update-readme.py` regenerates:
- `README.md` skills table
- `.claude-plugin/marketplace.json`
- `<skill>/.claude-plugin/plugin.json` for each skill

This runs automatically on push to main via GitHub Actions.

## Linting

```bash
skill-lint/scripts/lint-skills.sh          # check all skills
skill-lint/scripts/lint-skills.sh --fix    # auto-fix (creates missing plugin.json, openai.yaml, fixes names)
```

## Conventions

- Each skill is independent — no cross-project dependencies, no monorepo build system
- Directories and scripts use kebab-case; Python uses snake_case
- Configuration via environment variables or config files
- Skills document their own dependencies and setup in SKILL.md
