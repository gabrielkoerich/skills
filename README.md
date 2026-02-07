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
| [anchor-sealevel-attacks](#anchor-sealevel-attacks) | Audits Solana/Anchor programs for all 11 sealevel attack vectors. Use when auditing Solana smart contracts or reviewing Anchor programs for security. | See SKILL.md |
| [apple-calendar](#apple-calendar) | macOS Calendar.app integration (CRUD, search) | macOS |
| [beancount-analytics](#beancount-analytics) | Analyze Beancount ledgers with reusable CLI reports and question-driven queries. Use when user asks for last month/last 12 months reports, spending breakdowns, savings trends, or direct finance questions from a .bean ledger. | ** python3, beancount (`pip install beancount`) |
| [binance-prices](#binance-prices) | Real-time crypto prices from Binance public API | python3, curl |
| [bird](#bird) | X/Twitter access via bird CLI | [bird CLI](https://github.com/steipete/bird), Chrome |
| [camsnap](#camsnap) | Capture frames/clips from RTSP/ONVIF cameras | [camsnap CLI](https://camsnap.ai), ffmpeg |
| [elevenlabs-voices](#elevenlabs-voices) | Voice synthesis with 18 personas, 32 languages, SFX | python3, `ELEVEN_API_KEY` |
| [github](#github) | GitHub CLI for issues, PRs, CI runs, and API queries | [gh CLI](https://cli.github.com) |
| [github-secrets](#github-secrets) | Manage GitHub repo/org secrets via API | bun, `GITHUB_TOKEN` |
| [intelbras](#intelbras) | Monitor/control Intelbras alarm systems and cameras | python3, curl |
| [notes-review](#notes-review) | Analyze personal markdown notes and journals with qmd-powered semantic search plus weekly/monthly reflection reports. Use for questions like what was accomplished, what is pending, and whether work aligns with goals. | ** python3 **Recommended:** qmd CLI for semantic/local search |
| [openai-whisper](#openai-whisper) | Local speech-to-text transcription | [whisper CLI](https://github.com/openai/whisper) |
| [qmd](#qmd) | Local hybrid search for markdown notes and docs | [qmd CLI](https://github.com/tobi/qmd) |
| [solana-best-practices](#solana-best-practices) | Reviews Solana/Anchor programs for development best practices. Use when writing, reviewing, improving or auditing Solana smart contracts. 31 vulnerability patterns with 4 real-world case studies. | See SKILL.md |
| [things3](#things3) | Things 3 task manager via CLI (macOS) | [things CLI](https://github.com/ossianhempel/things3-cli), macOS |
| [tmux](#tmux) | Remote-control tmux sessions for interactive CLIs | tmux |
| [x-twitter-chrome](#x-twitter-chrome) | Read/search X via Chrome DevTools Protocol | bun, Chrome |
---

## Skill Details
### anchor-sealevel-attacks

Audits Solana/Anchor programs for all 11 sealevel attack vectors: missing signer authorization, account data mismatches, owner check gaps, type cosplay, re-initialization, arbitrary CPI, duplicate mutable accounts, bump seed canonicalization, PDA sharing, unsafe account closing, and sysvar address spoofing. Use when auditing Solana smart contracts or reviewing Anchor programs for security.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See anchor-sealevel-attacks/SKILL.md for full documentation
```

---

### apple-calendar

macOS Calendar.app integration via AppleScript. List calendars, create/read/update/delete events, search.

**Requirements:** macOS with Calendar.app
**Setup:** None
**Usage:**
```bash
scripts/cal-list.sh                    # List calendars
scripts/cal-events.sh 7                # Events for next 7 days
scripts/cal-create.sh "Work" "Meeting" "2025-01-15 10:00" "2025-01-15 11:00"
scripts/cal-search.sh "standup" 30
```

---

### beancount-analytics

Analyze Beancount ledgers with reusable CLI reports and question-driven queries. Use when user asks for last month/last 12 months reports, spending breakdowns, savings trends, or direct finance questions from a .bean ledger.

**Requirements:** ** python3, beancount (`pip install beancount`)
**Setup:** None
**Usage:**
```bash
# See beancount-analytics/SKILL.md for full documentation
```

---

### binance-prices

Fetch real-time cryptocurrency prices from Binance public API. No authentication needed.

**Requirements:** python3, curl
**Setup:** None
**Usage:**
```bash
scripts/price.sh btc                   # BTC price in USDT
scripts/price.sh eth btc               # ETH price in BTC
scripts/prices.sh btc eth sol          # Multiple prices
```

---

### bird

Read and search X (Twitter) using the bird CLI with Chrome cookie extraction.

**Requirements:** [bird CLI](https://github.com/steipete/bird), Chrome logged into x.com
**Setup:**
```bash
bun add -g @steipete/bird
```
**Usage:**
```bash
bird read https://x.com/user/status/123 --chrome-profile claude --plain
bird search "Solana traders" --limit 20 --chrome-profile claude
bird timeline @username --limit 10 --chrome-profile claude
```

---

### camsnap

Capture snapshots, clips, or motion events from RTSP/ONVIF cameras using the camsnap CLI.

**Requirements:** [camsnap CLI](https://camsnap.ai), ffmpeg
**Setup:**
```bash
# macOS
brew install steipete/tap/camsnap

# Configure a camera
camsnap add --name kitchen --host 192.168.0.10 --user user --pass pass
```
**Config:** `~/.config/camsnap/config.yaml`
**Usage:**
```bash
camsnap discover --info                              # Discover cameras on network
camsnap snap kitchen --out shot.jpg                  # Take a snapshot
camsnap clip kitchen --dur 5s --out clip.mp4         # Record a clip
camsnap watch kitchen --threshold 0.2 --action '...' # Motion detection
camsnap doctor --probe                               # Diagnose issues
```

---

### elevenlabs-voices

Voice synthesis toolkit with 18 voice personas, 32 languages, sound effects, batch processing, and voice design.

**Requirements:** python3
**Setup:**
```bash
./setup.sh elevenlabs-voices
# Or manually: add ELEVEN_API_KEY to .env
```
**Env vars:** `ELEVEN_API_KEY` — get one at [elevenlabs.io](https://elevenlabs.io)
**Usage:**
```bash
python3 scripts/tts.py --list                                          # List voices
python3 scripts/tts.py --text "Hello" --voice rachel --output hello.mp3
python3 scripts/tts.py --text "Bonjour" --voice adam --lang fr
python3 scripts/sfx.py --prompt "Thunder rumbling" --duration 5
python3 scripts/voice-design.py --gender female --age young --accent british
```

---

### github

Interact with GitHub using the `gh` CLI. Issues, PRs, CI runs, and API queries.

**Requirements:** [gh CLI](https://cli.github.com)
**Setup:**
```bash
# macOS
brew install gh

# Linux
apt install gh

# Authenticate
gh auth login
```
**Usage:**
```bash
gh pr checks 55 --repo owner/repo                   # Check CI status
gh run list --repo owner/repo --limit 10             # List workflow runs
gh run view <run-id> --repo owner/repo --log-failed  # View failed logs
gh issue list --repo owner/repo --json number,title   # List issues as JSON
gh api repos/owner/repo/pulls/55 --jq '.title'       # Direct API access
```

---

### github-secrets

Manage GitHub repository, organization, and environment secrets via the GitHub API with libsodium encryption.

**Requirements:** bun
**Setup:**
```bash
cd github-secrets && bun install
./setup.sh github-secrets
# Or manually: add GITHUB_TOKEN to .env
```
**Env vars:** `GITHUB_TOKEN` — needs `repo` and `admin:org` scopes
**Usage:**
```bash
bun run src/cli.ts list --owner myuser --repo myrepo
bun run src/cli.ts set --owner myuser --repo myrepo --name API_KEY --value "secret"
bun run src/cli.ts sync --owner myuser --repo myrepo --env-file .env
```
**Tests:**
```bash
bun test
```

---

### intelbras

Monitor and control Intelbras alarm systems (AMT series) and DVR cameras via HTTP API.

**Requirements:** python3, curl, ffmpeg (optional, for camera snapshots)
**Setup:**
```bash
./setup.sh intelbras
# Or manually: add INTELBRAS_* vars to .env
```
**Env vars:** `INTELBRAS_ALARM_HOST`, `INTELBRAS_ALARM_PORT`, `INTELBRAS_ALARM_USERNAME`, `INTELBRAS_ALARM_PASSWORD`, `INTELBRAS_DVR_HOST`, `INTELBRAS_DVR_PORT`, `INTELBRAS_DVR_RTSP_PORT`, `INTELBRAS_DVR_USERNAME`, `INTELBRAS_DVR_PASSWORD`

The setup script also creates `data/config.json` from the template for camera channel definitions.

**Usage:**
```bash
python3 scripts/intelbras-alarm.py status
python3 scripts/intelbras-alarm.py arm
python3 scripts/intelbras-alarm.py snap CAM1
python3 scripts/intelbras-alarm.py all-snap
```

---

### notes-review

Analyze personal markdown notes and journals with qmd-powered semantic search plus weekly/monthly reflection reports. Use for questions like what was accomplished, what is pending, and whether work aligns with goals.

**Requirements:** ** python3 **Recommended:** qmd CLI for semantic/local search
**Setup:** None
**Usage:**
```bash
# See notes-review/SKILL.md for full documentation
```

---

### openai-whisper

Local speech-to-text transcription using OpenAI's Whisper. Runs entirely offline after model download.

**Requirements:** whisper CLI
**Setup:**
```bash
# macOS
brew install openai-whisper

# Linux
pip install openai-whisper
```
**Usage:**
```bash
whisper audio.m4a --model turbo --output_dir .
whisper audio.mp3 --task translate          # Translate to English
./whisper-handler.sh audio.m4a txt /tmp     # Handler script
```

---

### qmd

Local hybrid search engine for markdown notes and docs. BM25 keyword search, vector semantic search, and LLM reranking — all running locally with no API keys.

**Requirements:** [qmd CLI](https://github.com/tobi/qmd), bun
**Setup:**
```bash
bun install -g https://github.com/tobi/qmd
qmd collection add /path/to/notes --name mynotes --mask "**/*.md"
qmd embed    # Enable semantic search
```
**Usage:**
```bash
qmd search "authentication flow" --json       # Fast keyword search
qmd vsearch "how does login work" --json      # Semantic search
qmd query "complex question" --json           # Hybrid with reranking
qmd get docs/guide.md --json                  # Retrieve document
```
**MCP Server:**
```bash
qmd mcp      # Exposes qmd_search, qmd_vsearch, qmd_query, qmd_get tools
```

---

### solana-best-practices

Reviews Solana/Anchor programs for development best practices. Use when writing, reviewing, improving or auditing Solana smart contracts. 31 vulnerability patterns with 4 real-world case studies.

**Requirements:** See SKILL.md
**Setup:** None
**Usage:**
```bash
# See solana-best-practices/SKILL.md for full documentation
```

---

### things3

Manage Things 3 tasks via the `things` CLI on macOS. Read from the local database, add/update todos via the Things URL scheme.

**Requirements:** [things CLI](https://github.com/ossianhempel/things3-cli), macOS
**Setup:**
```bash
GOBIN=/opt/homebrew/bin go install github.com/ossianhempel/things3-cli/cmd/things@latest
```
If DB reads fail, grant **Full Disk Access** to the calling app (e.g. Terminal).
**Usage:**
```bash
things inbox --limit 50                              # View inbox
things today                                         # Today's tasks
things search "query"                                # Search tasks
things projects                                      # List projects
things add "Buy milk" --when today                   # Add a todo
things add "Trip prep" --list "Travel" --tags "travel"
things --dry-run add "Test"                          # Preview without executing
```

---

### tmux

Remote-control tmux sessions for interactive CLIs. Send keystrokes, capture output, orchestrate parallel agents.

**Requirements:** tmux (macOS/Linux)
**Setup:**
```bash
# macOS
brew install tmux

# Linux
apt install tmux
```
**Usage:**
```bash
# Start a session
SOCKET="${TMPDIR:-/tmp}/agent-tmux-sockets/agent.sock"
tmux -S "$SOCKET" new -d -s mysession -n shell

# Send commands
tmux -S "$SOCKET" send-keys -t mysession -l -- 'echo hello' Enter

# Capture output
tmux -S "$SOCKET" capture-pane -p -J -t mysession -S -200

# Kill session
tmux -S "$SOCKET" kill-session -t mysession
```

---

### x-twitter-chrome

Read and search X (Twitter) using Chrome DevTools Protocol with a logged-in Chrome session.

**Requirements:** bun, Google Chrome
**Setup:**

Start Chrome with remote debugging:
```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir="$HOME/.claude/browser/<profile>/user-data" \
  --remote-debugging-port=18800

# Linux
google-chrome --user-data-dir="$HOME/.claude/browser/<profile>/user-data" --remote-debugging-port=18800
```

Log into x.com in the browser, then:
```bash
bun run timeline.ts @username
bun run read.ts https://x.com/user/status/123
bun run search.ts "query"
bun run bookmarks.ts
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
