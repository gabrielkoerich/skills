# Skills

[![Update README](https://github.com/gabrielkoerich/skills/actions/workflows/update-readme.yml/badge.svg)](https://github.com/gabrielkoerich/skills/actions/workflows/update-readme.yml)

A collection of independent, self-contained skills for AI agents. Each skill lives in its own directory with a `SKILL.md` documentation file. No skill files need to be modified — all configuration is done via environment variables in a gitignored `.env` file.

> **Security:** Always review a skill's code before installing it. Do not run code you haven't verified. Skills can contain scripts that execute on your machine — understand what they do first.

## Quick Start

```bash
git clone https://github.com/gabrielkoerich/skills.git
cd skills

# Interactive setup — checks dependencies, prompts for API keys, runs smoke tests
./setup.sh

# Or set up a single skill
./setup.sh binance-prices
```

The setup script writes environment variables to `.env` at the repo root (gitignored). Source it to make them available:

```bash
source .env

# Or add to your shell profile for persistence
echo "source $(pwd)/.env" >> ~/.zshrc
```

## Installing Skills on Your Agent

Each skill follows the [Agent Skills](https://agentskills.io) open standard (`SKILL.md` + optional scripts/resources), so it works with any agent that supports it.

**Quickest way:** Send your agent this repository and ask it to install the skill you need. It will handle the setup automatically. Just remember to run `./setup.sh <skill-name>` afterwards to configure dependencies and environment variables.

### Claude Code

Copy or symlink the skill directory into your Claude Code skills folder:

```bash
# Personal (available across all projects)
cp -r github-secrets ~/.claude/skills/github-secrets

# Or project-level (available in this project only)
cp -r github-secrets .claude/skills/github-secrets
```

Then run setup for dependencies and API keys:
```bash
./setup.sh github-secrets
source .env
```

### Codex (OpenAI)

Copy or symlink the skill directory into your Codex skills folder:

```bash
# Project-level
cp -r github-secrets .agents/skills/github-secrets

# Or user-level
cp -r github-secrets ~/.agents/skills/github-secrets
```

Then run setup:
```bash
./setup.sh github-secrets
source .env
```

### OpenClaw

Paste this repository's URL into your OpenClaw chat and ask it to install the skill, or copy manually into your workspace skills folder:

```bash
# Find your workspace path
cat ~/.openclaw/openclaw.json | grep workspace

# Copy into your workspace skills folder
cp -r github-secrets <workspace>/skills/github-secrets
```

Then run setup:
```bash
./setup.sh github-secrets
source .env
```

### Other Agents

For any agent that supports `SKILL.md` files, copy the skill directory into the agent's skills folder and run the setup script to configure dependencies and environment variables.

---

## Available Skills

| Skill | Description | Requirements |
|-------|-------------|--------------|
| [act](#act) | Run GitHub Actions workflows locally using act. Test CI pipelines, debug jobs, and validate workflows before pushing. | See SKILL.md |
| [apple-calendar](#apple-calendar) | macOS Calendar.app integration (CRUD, search) | macOS |
| [beancount-analytics](#beancount-analytics) | Analyze Beancount ledgers with reusable CLI reports and question-driven queries. Use when user asks for last month/last 12 months reports, spending breakdowns, savings trends, or direct finance questions from a .bean ledger. | ** python3, beancount (`pip install beancount`) |
| [binance-prices](#binance-prices) | Real-time crypto prices from Binance public API | python3, curl |
| [camsnap](#camsnap) | Capture frames/clips from RTSP/ONVIF cameras | [camsnap CLI](https://camsnap.ai), ffmpeg |
| [contract-decoder](https://github.com/gabrielkoerich/skills/tree/main/contract-decoder) | Decode and reverse-engineer smart contract binaries for security research. Solana: extract instructions, discriminators, PDAs, and error codes from .so files. EVM: decompile bytecode to recover function selectors and storage layout. Use for bug bounty recon, verifying deployed code, or analyzing closed-source contracts. | See SKILL.md |
| [contract-decoder](https://github.com/gabrielkoerich/skills/tree/main/contract-decoder) | Decode and reverse-engineer smart contract binaries for security research. Solana: extract instructions, discriminators, PDAs, and error codes from .so files. EVM: decompile bytecode to recover function selectors and storage layout. Use for bug bounty recon, verifying deployed code, or analyzing closed-source contracts. | See SKILL.md |
| [contract-decoder](https://github.com/gabrielkoerich/skills/tree/main/contract-decoder) | Decode and reverse-engineer smart contract binaries for security research. Solana: extract instructions, discriminators, PDAs, and error codes from .so files. EVM: decompile bytecode to recover function selectors and storage layout. Use for bug bounty recon, verifying deployed code, or analyzing closed-source contracts. | See SKILL.md |
| [conventional-commits](#conventional-commits) | Conventional Commits specification is a lightweight convention on top of commit messages. It provides an easy set of rules for creating an explicit commit history, which makes it easier to write automated tools on top of. This convention dovetails with [SemVer](http://semver.org), by describing the features, fixes, and breaking changes made in commit messages. | See SKILL.md |
| [elevenlabs-voices](#elevenlabs-voices) | Voice synthesis with 18 personas, 32 languages, SFX | python3, `ELEVEN_API_KEY` |
| [evm-contract-audit](#evm-contract-audit) | Audits EVM/Solidity smart contracts for security vulnerabilities. Covers reentrancy, access control, flash loan exploits, upgrade issues, oracle manipulation, signature attacks, and more. Learned from EVMbench (120 real Code4rena vulnerabilities across 40 production codebases). | See SKILL.md |
| [gh-issue-worktree](#gh-issue-worktree) | Manage Git worktrees for isolated development environments per GitHub issue. Use `gh issue develop` to register linked branches and `git worktree` for isolated directories. | See SKILL.md |
| [gh-pr-polish](#gh-pr-polish) | Generate high-signal PR titles and bodies from git history and changed files, then open PRs with gh CLI. | See SKILL.md |
| [git-worktree-cleaner](#git-worktree-cleaner) | Audit and clean git worktrees safely across repositories, including stale metadata and merged local branches. | See SKILL.md |
| [git-worktrees](#git-worktrees) | Manage plain Git worktree feature branches without issue linking. Create a feature branch worktree, develop in isolation, push, and open a PR with commit-based changes summary. | See SKILL.md |
| [github](#github) | GitHub CLI for issues, PRs, CI runs, and API queries | [gh CLI](https://cli.github.com) |
| [github-secrets](#github-secrets) | Manage GitHub repo/org secrets via API | bun, `GITHUB_TOKEN` |
| [intelbras](#intelbras) | Monitor/control Intelbras alarm systems and cameras | python3, curl |
| [notes-review](#notes-review) | Analyze personal markdown notes and journals with qmd-powered semantic search plus weekly/monthly reflection reports. Use for questions like what was accomplished, what is pending, and whether work aligns with goals. | ** python3 **Recommended:** qmd CLI for semantic/local search |
| [openai-whisper](#openai-whisper) | Local speech-to-text transcription | [whisper CLI](https://github.com/openai/whisper) |
| [qmd](#qmd) | Local hybrid search for markdown notes and docs | [qmd CLI](https://github.com/tobi/qmd) |
| [skill-lint](#skill-lint) | Lint and auto-fix skill folders for metadata, naming consistency, path placeholder consistency, and optional agents/openai.yaml presence. | See SKILL.md |
| [solana-best-practices](#solana-best-practices) | Reviews Solana/Anchor programs for development best practices. Use when writing, reviewing, improving or auditing Solana smart contracts. 31 vulnerability patterns with 4 real-world case studies. | See SKILL.md |
| [solana-dev](https://github.com/gabrielkoerich/skills/tree/main/solana-dev) | End-to-end Solana development playbook (Jan 2026). Prefer Solana Foundation framework-kit (@solana/client + @solana/react-hooks) for React/Next.js UI. Prefer @solana/kit for all new client/RPC/transaction code. When legacy dependencies require web3.js, isolate it behind @solana/web3-compat (or @solana/web3.js as a true legacy fallback). Covers wallet-standard-first connection (incl. ConnectorKit), Anchor/Pinocchio programs, Codama-based client generation, LiteSVM/Mollusk/Surfpool testing, and security checklists. | See SKILL.md |
| [solana-dev](https://github.com/gabrielkoerich/skills/tree/main/solana-dev) | End-to-end Solana development playbook (Jan 2026). Prefer Solana Foundation framework-kit (@solana/client + @solana/react-hooks) for React/Next.js UI. Prefer @solana/kit for all new client/RPC/transaction code. When legacy dependencies require web3.js, isolate it behind @solana/web3-compat (or @solana/web3.js as a true legacy fallback). Covers wallet-standard-first connection (incl. ConnectorKit), Anchor/Pinocchio programs, Codama-based client generation, LiteSVM/Mollusk/Surfpool testing, and security checklists. | See SKILL.md |
| [solana-dev](https://github.com/gabrielkoerich/skills/tree/main/solana-dev) | End-to-end Solana development playbook (Jan 2026). Prefer Solana Foundation framework-kit (@solana/client + @solana/react-hooks) for React/Next.js UI. Prefer @solana/kit for all new client/RPC/transaction code. When legacy dependencies require web3.js, isolate it behind @solana/web3-compat (or @solana/web3.js as a true legacy fallback). Covers wallet-standard-first connection (incl. ConnectorKit), Anchor/Pinocchio programs, Codama-based client generation, LiteSVM/Mollusk/Surfpool testing, and security checklists. | See SKILL.md |
| [solana-security-audit](#solana-security-audit) | Audits Solana/Anchor programs for all 11 sealevel attack vectors. Use when auditing Solana smart contracts or reviewing Anchor programs for security. | See SKILL.md |
| [things3](#things3) | Things 3 task manager via CLI (macOS) | [things CLI](https://github.com/ossianhempel/things3-cli), macOS |
| [tmux](#tmux) | Remote-control tmux sessions for interactive CLIs | tmux |
| [x-twitter-chrome](#x-twitter-chrome) | Read/search X via Chrome DevTools Protocol | bun, Chrome |
---

## Skill Details
### [act](https://github.com/gabrielkoerich/skills/tree/main/act)

Run GitHub Actions workflows locally using act. Test CI pipelines, debug jobs, and validate workflows before pushing.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See act/SKILL.md for full documentation
```

---

### [apple-calendar](https://github.com/gabrielkoerich/skills/tree/main/apple-calendar)

Apple Calendar.app integration for macOS. CRUD operations for events, search, and multi-calendar support.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See apple-calendar/SKILL.md for full documentation
```

---

### [beancount-analytics](https://github.com/gabrielkoerich/skills/tree/main/beancount-analytics)

Analyze Beancount ledgers with reusable CLI reports and question-driven queries. Use when user asks for last month/last 12 months reports, spending breakdowns, savings trends, or direct finance questions from a .bean ledger.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See beancount-analytics/SKILL.md for full documentation
```

---

### [binance-prices](https://github.com/gabrielkoerich/skills/tree/main/binance-prices)

Fetch cryptocurrency prices from Binance public API (no API key required). Use when user asks for BTC, ETH, SOL, or any crypto price from Binance.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See binance-prices/SKILL.md for full documentation
```

---

### [camsnap](https://github.com/gabrielkoerich/skills/tree/main/camsnap)

Capture frames or clips from RTSP/ONVIF cameras.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See camsnap/SKILL.md for full documentation
```

---

### [contract-decoder](https://github.com/gabrielkoerich/skills/tree/main/contract-decoder)

Decode and reverse-engineer smart contract binaries for security research. Solana: extract instructions, discriminators, PDAs, and error codes from .so files. EVM: decompile bytecode to recover function selectors and storage layout. Use for bug bounty recon, verifying deployed code, or analyzing closed-source contracts.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See contract-decoder/SKILL.md for full documentation
```

---

### [conventional-commits](https://github.com/gabrielkoerich/skills/tree/main/conventional-commits)

Conventional Commits specification is a lightweight convention on top of commit messages. It provides an easy set of rules for creating an explicit commit history, which makes it easier to write automated tools on top of. This convention dovetails with [SemVer](http://semver.org), by describing the features, fixes, and breaking changes made in commit messages.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See conventional-commits/SKILL.md for full documentation
```

---

### [elevenlabs-voices](https://github.com/gabrielkoerich/skills/tree/main/elevenlabs-voices)

High-quality voice synthesis with 18 personas, 32 languages, sound effects, batch processing, and voice design using ElevenLabs API.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See elevenlabs-voices/SKILL.md for full documentation
```

---

### [evm-contract-audit](https://github.com/gabrielkoerich/skills/tree/main/evm-contract-audit)

Audits EVM/Solidity smart contracts for security vulnerabilities. Covers reentrancy, access control, flash loan exploits, upgrade issues, oracle manipulation, signature attacks, and more. Learned from EVMbench (120 real Code4rena vulnerabilities across 40 production codebases).

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See evm-contract-audit/SKILL.md for full documentation
```

---

### [gh-issue-worktree](https://github.com/gabrielkoerich/skills/tree/main/gh-issue-worktree)

Manage Git worktrees for isolated development environments per GitHub issue. Use `gh issue develop` to register linked branches and `git worktree` for isolated directories.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See gh-issue-worktree/SKILL.md for full documentation
```

---

### [gh-pr-polish](https://github.com/gabrielkoerich/skills/tree/main/gh-pr-polish)

Generate high-signal PR titles and bodies from git history and changed files, then open PRs with gh CLI.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See gh-pr-polish/SKILL.md for full documentation
```

---

### [git-worktree-cleaner](https://github.com/gabrielkoerich/skills/tree/main/git-worktree-cleaner)

Audit and clean git worktrees safely across repositories, including stale metadata and merged local branches.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See git-worktree-cleaner/SKILL.md for full documentation
```

---

### [git-worktrees](https://github.com/gabrielkoerich/skills/tree/main/git-worktrees)

Manage plain Git worktree feature branches without issue linking. Create a feature branch worktree, develop in isolation, push, and open a PR with commit-based changes summary.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See git-worktrees/SKILL.md for full documentation
```

---

### [github](https://github.com/gabrielkoerich/skills/tree/main/github)

Interact with GitHub using the `gh` CLI. Use `gh issue`, `gh pr`, `gh run`, and `gh api` for issues, PRs, CI runs, and advanced queries.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See github/SKILL.md for full documentation
```

---

### [github-secrets](https://github.com/gabrielkoerich/skills/tree/main/github-secrets)

Manage GitHub repository secrets via the GitHub API. Supports listing, adding, updating, and deleting repository and organization secrets. Use when user needs to manage GitHub Actions secrets, environment variables, or repository-level secrets securely.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See github-secrets/SKILL.md for full documentation
```

---

### [intelbras](https://github.com/gabrielkoerich/skills/tree/main/intelbras)

Monitor and control Intelbras alarm systems and cameras. Supports AMT series, Intelbras IFR alarms with HTTP API. Get status, arm/disarm, and check camera streams.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See intelbras/SKILL.md for full documentation
```

---

### [notes-review](https://github.com/gabrielkoerich/skills/tree/main/notes-review)

Analyze personal markdown notes and journals with qmd-powered semantic search plus weekly/monthly reflection reports. Use for questions like what was accomplished, what is pending, and whether work aligns with goals.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See notes-review/SKILL.md for full documentation
```

---

### [openai-whisper](https://github.com/gabrielkoerich/skills/tree/main/openai-whisper)

Local speech-to-text with the Whisper CLI (no API key).

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See openai-whisper/SKILL.md for full documentation
```

---

### [qmd](https://github.com/gabrielkoerich/skills/tree/main/qmd)

Fast local search for markdown files, notes, and docs using qmd CLI. Combines BM25 full-text search, vector semantic search, and LLM reranking — all running locally. No API keys needed.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See qmd/SKILL.md for full documentation
```

---

### [skill-lint](https://github.com/gabrielkoerich/skills/tree/main/skill-lint)

Lint and auto-fix skill folders for metadata, naming consistency, path placeholder consistency, and optional agents/openai.yaml presence.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See skill-lint/SKILL.md for full documentation
```

---

### [solana-best-practices](https://github.com/gabrielkoerich/skills/tree/main/solana-best-practices)

Reviews Solana/Anchor programs for development best practices. Use when writing, reviewing, improving or auditing Solana smart contracts. 31 vulnerability patterns with 4 real-world case studies.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See solana-best-practices/SKILL.md for full documentation
```

---

### [solana-dev](https://github.com/gabrielkoerich/skills/tree/main/solana-dev)

End-to-end Solana development playbook (Jan 2026). Prefer Solana Foundation framework-kit (@solana/client + @solana/react-hooks) for React/Next.js UI. Prefer @solana/kit for all new client/RPC/transaction code. When legacy dependencies require web3.js, isolate it behind @solana/web3-compat (or @solana/web3.js as a true legacy fallback). Covers wallet-standard-first connection (incl. ConnectorKit), Anchor/Pinocchio programs, Codama-based client generation, LiteSVM/Mollusk/Surfpool testing, and security checklists.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See solana-dev/SKILL.md for full documentation
```

---

### [solana-security-audit](https://github.com/gabrielkoerich/skills/tree/main/solana-security-audit)

Comprehensive Solana smart contract security auditor. Covers 25+ attack vectors across Anchor, native Rust, and Pinocchio: sealevel attacks, arithmetic safety, CPI exploits, state machine issues, Token-2022 risks, and real-world case studies.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See solana-security-audit/SKILL.md for full documentation
```

---

### [things3](https://github.com/gabrielkoerich/skills/tree/main/things3)

Manage Things 3 via the `things` CLI on macOS (add/update projects+todos via URL scheme; read/search/list from the local Things database). Use when a user asks to add a task to Things, list inbox/today/upcoming, search tasks, or inspect projects/areas/tags.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See things3/SKILL.md for full documentation
```

---

### [tmux](https://github.com/gabrielkoerich/skills/tree/main/tmux)

Remote-control tmux sessions for interactive CLIs by sending keystrokes and scraping pane output.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See tmux/SKILL.md for full documentation
```

---

### [x-twitter-chrome](https://github.com/gabrielkoerich/skills/tree/main/x-twitter-chrome)

Read and search X/Twitter using Chrome browser automation with an authenticated local profile.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See x-twitter-chrome/SKILL.md for full documentation
```

## Structure

```
skills/
├── .env              # Your config (gitignored, created by setup.sh)
├── .env.example      # Template (committed)
├── setup.sh          # Interactive setup script
├── CLAUDE.md         # Agent guidance
├── README.md         # This file
└── skill-name/
    ├── SKILL.md      # Skill documentation
    ├── scripts/      # Executable scripts
    └── src/          # Source code (TypeScript projects)
```
