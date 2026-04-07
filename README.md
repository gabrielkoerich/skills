# Skills

[![Readme Update](https://github.com/gabrielkoerich/skills/actions/workflows/update-readme.yml/badge.svg)](https://github.com/gabrielkoerich/skills/actions/workflows/update-readme.yml)

A collection of independent, self-contained skills for AI agents. Each skill lives in its own directory with a `SKILL.md` documentation file.

Some skills require external dependencies or environment variables — check each skill's `SKILL.md` for setup instructions.

> **Security:** Always review a skill's code before installing it. Do not run code you haven't verified. Skills can contain scripts that execute on your machine — understand what they do first.

## Installing Skills

Each skill follows the [Agent Skills](https://agentskills.io) open standard (`SKILL.md` + optional scripts/resources), so it works with any agent that supports it.

### Claude Code (Plugin Marketplace)

This repo is a Claude Code plugin marketplace. Add it and install individual skills:

```bash
# Add the marketplace
/plugin marketplace add gabrielkoerich/skills

# Install a skill
/plugin install github-issue-worktree@skills

# Update all installed skills
/plugin marketplace update
```

### Claude

```bash
git clone https://github.com/gabrielkoerich/skills.git && cd skills

# Personal (available across all projects)
cp -r github-secrets ~/.claude/skills/github-secrets

# Or project-level (available in this project only)
cp -r github-secrets .claude/skills/github-secrets
```

### Codex

```bash
git clone https://github.com/gabrielkoerich/skills.git && cd skills

# Project-level
cp -r github-secrets .agents/skills/github-secrets

# Or user-level
cp -r github-secrets ~/.agents/skills/github-secrets
```

### Other Agents

For any agent that supports `SKILL.md` files, copy the skill directory into the agent's skills folder.

## Available Skills

| Skill | Description | Requirements |
|-------|-------------|--------------|
| [act](https://github.com/gabrielkoerich/skills/blob/main/act/SKILL.md) | Run GitHub Actions workflows locally using act. Test CI pipelines, debug jobs, and validate workflows before pushing. | See SKILL.md |
| [apple-calendar](https://github.com/gabrielkoerich/skills/blob/main/apple-calendar/SKILL.md) | Apple Calendar.app integration for macOS. CRUD operations for events, search, and multi-calendar support. | See SKILL.md |
| [beancount-analytics](https://github.com/gabrielkoerich/skills/blob/main/beancount-analytics/SKILL.md) | Analyze Beancount ledgers with reusable CLI reports and question-driven queries. Use when user asks for last month/last 12 months reports, spending breakdowns, savings trends, or direct finance questions from a .bean ledger. | See SKILL.md |
| [binance-prices](https://github.com/gabrielkoerich/skills/blob/main/binance-prices/SKILL.md) | Fetch cryptocurrency prices from Binance public API (no API key required). Use when user asks for BTC, ETH, SOL, or any crypto price from Binance. | See SKILL.md |
| [bird](https://github.com/gabrielkoerich/skills/blob/main/bird/SKILL.md) | bird is a fast X CLI for tweeting, replying, and reading via X/Twitter GraphQL (cookie auth). Requires bird cli installed (bun add -g @steipete/bird) | See SKILL.md |
| [camsnap](https://github.com/gabrielkoerich/skills/blob/main/camsnap/SKILL.md) | Capture frames or clips from RTSP/ONVIF cameras. | See SKILL.md |
| [conventional-commits](https://github.com/gabrielkoerich/skills/blob/main/conventional-commits/SKILL.md) | Conventional Commits specification is a lightweight convention on top of commit messages. It provides an easy set of rules for creating an explicit commit history, which makes it easier to write automated tools on top of. This convention dovetails with [SemVer](http://semver.org), by describing the features, fixes, and breaking changes made in commit messages. | See SKILL.md |
| [elevenlabs-voices](https://github.com/gabrielkoerich/skills/tree/main/elevenlabs-voices) | High-quality voice synthesis with 18 personas, 32 languages, sound effects, batch processing, and voice design using ElevenLabs API. | See SKILL.md |
| [evm-contract-audit](https://github.com/gabrielkoerich/skills/tree/main/evm-contract-audit) | Audits EVM/Solidity smart contracts for security vulnerabilities. Covers reentrancy, access control, flash loan exploits, upgrade issues, oracle manipulation, signature attacks, and more. Learned from EVMbench (120 real Code4rena vulnerabilities across 40 production codebases). | See SKILL.md |
| [git-worktrees](https://github.com/gabrielkoerich/skills/blob/main/git-worktrees/SKILL.md) | Manage plain Git worktree feature branches without issue linking. Create a feature branch worktree, develop in isolation, push, and open a PR with commit-based changes summary. | See SKILL.md |
| [github](https://github.com/gabrielkoerich/skills/blob/main/github/SKILL.md) | Interact with GitHub using the `gh` CLI. Use `gh issue`, `gh pr`, `gh run`, and `gh api` for issues, PRs, CI runs, and advanced queries. | See SKILL.md |
| [github-issue-worktree](https://github.com/gabrielkoerich/skills/blob/main/github-issue-worktree/SKILL.md) | Manage Git worktrees for isolated development environments per GitHub issue. Use `gh issue develop` to register linked branches and `git worktree` for isolated directories. Use it when the user explicity ask to work in a given github issue. | See SKILL.md |
| [github-secrets](https://github.com/gabrielkoerich/skills/tree/main/github-secrets) | Manage GitHub repository secrets via the GitHub API. Supports listing, adding, updating, and deleting repository and organization secrets. Use when user needs to manage GitHub Actions secrets, environment variables, or repository-level secrets securely. | See SKILL.md |
| [intelbras](https://github.com/gabrielkoerich/skills/blob/main/intelbras/SKILL.md) | Monitor and control Intelbras alarm systems and cameras. Supports AMT series, Intelbras IFR alarms with HTTP API. Get status, arm/disarm, and check camera streams. | See SKILL.md |
| [openai-whisper](https://github.com/gabrielkoerich/skills/tree/main/openai-whisper) | Local speech-to-text with the Whisper CLI (no API key). | See SKILL.md |
| [qmd](https://github.com/gabrielkoerich/skills/blob/main/qmd/SKILL.md) | Fast local search for markdown files, notes, and docs using qmd CLI. Combines BM25 full-text search, vector semantic search, and LLM reranking — all running locally. No API keys needed. | See SKILL.md |
| [skill-lint](https://github.com/gabrielkoerich/skills/blob/main/skill-lint/SKILL.md) | Lint and auto-fix skill folders for metadata, naming consistency, path placeholder consistency, and optional agents/openai.yaml presence. | See SKILL.md |
| [solana-best-practices](https://github.com/gabrielkoerich/skills/tree/main/solana-best-practices) | Reviews Solana/Anchor programs for development best practices. Use when writing, reviewing, improving or auditing Solana smart contracts. 31 vulnerability patterns with 4 real-world case studies. | See SKILL.md |
| [solana-dev](https://github.com/gabrielkoerich/skills/blob/main/solana-dev/SKILL.md) | End-to-end Solana development playbook (Jan 2026). Prefer Solana Foundation framework-kit (@solana/client + @solana/react-hooks) for React/Next.js UI. Prefer @solana/kit for all new client/RPC/transaction code. When legacy dependencies require web3.js, isolate it behind @solana/web3-compat (or @solana/web3.js as a true legacy fallback). Covers wallet-standard-first connection (incl. ConnectorKit), Anchor/Pinocchio programs, Codama-based client generation, LiteSVM/Mollusk/Surfpool testing, and security checklists. | See SKILL.md |
| [solana-security-audit](https://github.com/gabrielkoerich/skills/tree/main/solana-security-audit) | Comprehensive Solana smart contract security auditor. Covers 25+ attack vectors across Anchor, native Rust, and Pinocchio: sealevel attacks, arithmetic safety, CPI exploits, state machine issues, Token-2022 risks, and real-world case studies. | See SKILL.md |
| [things3](https://github.com/gabrielkoerich/skills/blob/main/things3/SKILL.md) | Manage Things 3 via the `things` CLI on macOS (add/update projects+todos via URL scheme; read/search/list from the local Things database). Use when a user asks to add a task to Things, list inbox/today/upcoming, search tasks, or inspect projects/areas/tags. | See SKILL.md |
| [tmux](https://github.com/gabrielkoerich/skills/blob/main/tmux/SKILL.md) | Remote-control tmux sessions for interactive CLIs by sending keystrokes and scraping pane output. | See SKILL.md |
| [x-twitter-brave](https://github.com/gabrielkoerich/skills/blob/main/x-twitter-brave/SKILL.md) | Read and search X/Twitter using Brave browser automation with an authenticated local profile. | See SKILL.md |
| [x-twitter-chrome](https://github.com/gabrielkoerich/skills/blob/main/x-twitter-chrome/SKILL.md) | Read and search X/Twitter using Chrome browser automation with an authenticated local profile. | See SKILL.md |

## Structure

```
skills/
├── CLAUDE.md         # Agent guidance
├── README.md         # This file
└── skill-name/
    ├── SKILL.md      # Skill documentation
    ├── scripts/      # Executable scripts
    └── src/          # Source code (TypeScript projects)
```
