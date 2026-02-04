# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **skill library** — a collection of independent, self-contained skill modules designed for integration with any AI agent (e.g. Claude). Each skill lives in its own directory with isolated dependencies and a standardized `SKILL.md` documentation file.

## Architecture

### Skill Structure Convention

Every skill follows this pattern:
```
skill-name/
├── SKILL.md          # Documentation (required)
├── scripts/          # Executable scripts (bash/python)
├── src/              # Source code (TypeScript projects)
└── [config files]    # .env.example, config.json, etc.
```

### SKILL.md Standard

Each SKILL.md contains YAML frontmatter with `name` and `description`, followed by documentation.

### Language Ecosystem

- **Bash**: System integration, CLI wrappers (apple-calendar, binance-prices, intelbras, openai-whisper, tmux)
- **Python 3.10+**: API clients, data processing (elevenlabs-voices, intelbras)
- **TypeScript/Bun**: Typed CLI tools (github-secrets, x-twitter-chrome)
- **Go CLI wrappers**: things3
- **AppleScript**: macOS Calendar.app integration (apple-calendar)
- **External CLI wrappers**: camsnap, github (gh), qmd, bird
- **Documentation-only**: Pure prompt skills (daily-plan, skill-creator)

### Key Integration Points

- **Agent config**: Environment files stored in `~/.claude/`
- **Chrome CDP**: x-twitter-chrome and bird use Chrome DevTools Protocol on port 18800 with a configured Chrome profile
- **External CLIs**: qmd, bird, gh, camsnap, things, openai-whisper are wrappers around installed tools
- **tmux**: Session management for interactive CLIs and parallel agent orchestration

## Project-Specific Commands

### github-secrets (TypeScript/Bun)
```bash
cd github-secrets
bun install
bun run build          # compile TypeScript
bun test               # run test suite
bun run src/cli.ts     # run CLI directly
```

### elevenlabs-voices (Python)
```bash
cd elevenlabs-voices
pip install elevenlabs  # dependency
python scripts/tts.py   # text-to-speech
python scripts/sfx.py   # sound effects
```

### x-twitter-chrome (TypeScript/Bun)
```bash
cd x-twitter-chrome
bun install
bun run timeline.ts    # read timelines
bun run search.ts      # search tweets
```

## Conventions

- No monorepo build system — each skill is independent with no cross-project dependencies
- Project directories use kebab-case; shell scripts use kebab-case; Python uses snake_case
- Configuration via environment variables (preferred) or config files (.env, config.json)
- .env.example files document required variables without exposing secrets
