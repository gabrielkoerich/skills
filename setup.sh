#!/bin/bash
# Interactive setup script for skills
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }
warn() { echo -e "  ${YELLOW}!${NC} $1"; }
info() { echo -e "  ${BLUE}→${NC} $1"; }

# Ensure env file exists
touch "$ENV_FILE"

source_env() {
    [ -f "$ENV_FILE" ] && source "$ENV_FILE"
}

save_env() {
    local key="$1" value="$2"
    # Remove existing line if present
    if grep -q "^export $key=" "$ENV_FILE" 2>/dev/null; then
        local tmp="$ENV_FILE.tmp"
        grep -v "^export $key=" "$ENV_FILE" > "$tmp"
        mv "$tmp" "$ENV_FILE"
    fi
    echo "export $key=\"$value\"" >> "$ENV_FILE"
    export "$key=$value"
    ok "Saved $key to $ENV_FILE"
}

check_bin() {
    if command -v "$1" &>/dev/null; then
        ok "$1 found: $(command -v "$1")"
        return 0
    else
        fail "$1 not found"
        return 1
    fi
}

prompt_env() {
    local key="$1" desc="$2" current=""
    source_env
    current="${!key}"
    if [ -n "$current" ]; then
        ok "$key is already set"
        read -p "  Keep current value? [Y/n] " keep
        [ "${keep,,}" = "n" ] || return 0
    fi
    read -p "  Enter $desc: " value
    if [ -n "$value" ]; then
        save_env "$key" "$value"
    else
        warn "Skipped $key"
    fi
}

header() {
    echo ""
    echo -e "${BOLD}━━━ $1 ━━━${NC}"
}

# ── Skill setup functions ───────────────────────────────────────

setup_apple_calendar() {
    header "apple-calendar"
    if [[ "$(uname)" != "Darwin" ]]; then
        fail "macOS only — skipping on $(uname)"
        return 1
    fi
    check_bin osascript || return 1

    info "Smoke test: listing calendars..."
    if "$SCRIPT_DIR/apple-calendar/scripts/cal-list.sh" &>/dev/null; then
        ok "apple-calendar works"
    else
        fail "Could not list calendars"
        return 1
    fi
}

setup_binance_prices() {
    header "binance-prices"
    check_bin python3 || return 1
    check_bin curl || return 1

    info "Smoke test: fetching BTC price..."
    local result
    result=$("$SCRIPT_DIR/binance-prices/scripts/price.sh" btc 2>&1)
    if echo "$result" | grep -q "BTCUSDT"; then
        ok "$result"
    else
        fail "Could not fetch price"
        return 1
    fi
}

setup_beancount_analytics() {
    header "beancount-analytics"
    check_bin python3 || return 1
    check_bin uv || { info "Install uv: https://docs.astral.sh/uv/getting-started/installation/"; return 1; }

    info "Installing Beancount dependency with uv..."
    if uv pip install --system beancount &>/dev/null; then
        ok "beancount installed"
    else
        warn "uv install failed"
        info "Try manually: uv pip install --system beancount"
        return 1
    fi

    info "Smoke test: report help..."
    if python3 "$SCRIPT_DIR/beancount-analytics/scripts/report.py" --help &>/dev/null; then
        ok "beancount-analytics works"
    else
        fail "beancount-analytics smoke test failed"
        return 1
    fi
}

setup_bird() {
    header "bird"
    if ! check_bin bird; then
        info "Install with: bun add -g @steipete/bird"
        read -p "  Install now? [y/N] " yn
        if [ "${yn,,}" = "y" ]; then
            bun add -g @steipete/bird
            check_bin bird || return 1
        else
            return 1
        fi
    fi
    warn "Requires Chrome profile logged into x.com"
}

setup_camsnap() {
    header "camsnap"
    if ! check_bin camsnap; then
        if [[ "$(uname)" == "Darwin" ]]; then
            info "Install with: brew install steipete/tap/camsnap"
            read -p "  Install now? [y/N] " yn
            if [ "${yn,,}" = "y" ]; then
                brew install steipete/tap/camsnap
                check_bin camsnap || return 1
            else
                return 1
            fi
        else
            fail "See https://camsnap.ai for installation"
            return 1
        fi
    fi
    check_bin ffmpeg || warn "ffmpeg not found — needed for captures"
    ok "camsnap ready"
}

setup_elevenlabs_voices() {
    header "elevenlabs-voices"
    check_bin python3 || return 1

    info "Smoke test: listing voices..."
    if python3 "$SCRIPT_DIR/elevenlabs-voices/scripts/tts.py" --list &>/dev/null; then
        ok "Voice list works"
    else
        fail "Could not list voices"
        return 1
    fi

    prompt_env "ELEVEN_API_KEY" "ElevenLabs API key (from https://elevenlabs.io)"
}

setup_github() {
    header "github"
    if ! check_bin gh; then
        if [[ "$(uname)" == "Darwin" ]]; then
            info "Install with: brew install gh"
        else
            info "Install with: apt install gh"
        fi
        read -p "  Install now? [y/N] " yn
        if [ "${yn,,}" = "y" ]; then
            if [[ "$(uname)" == "Darwin" ]]; then
                brew install gh
            else
                sudo apt install -y gh
            fi
            check_bin gh || return 1
        else
            return 1
        fi
    fi

    info "Checking auth status..."
    if gh auth status &>/dev/null; then
        ok "gh is authenticated"
    else
        warn "gh is not authenticated"
        info "Run: gh auth login"
    fi
}

setup_github_secrets() {
    header "github-secrets"
    check_bin bun || return 1

    info "Installing dependencies..."
    (cd "$SCRIPT_DIR/github-secrets" && bun install --silent)
    ok "Dependencies installed"

    info "Smoke test: CLI help..."
    if (cd "$SCRIPT_DIR/github-secrets" && bun run src/cli.ts --help &>/dev/null); then
        ok "CLI works"
    else
        fail "CLI failed"
        return 1
    fi

    prompt_env "GITHUB_TOKEN" "GitHub Personal Access Token (scopes: repo, admin:org)"
}

setup_intelbras() {
    header "intelbras"
    check_bin python3 || return 1
    check_bin curl || return 1

    # Ensure config.json exists (gitignored, so copy from example for new clones)
    local config_file="$SCRIPT_DIR/intelbras/data/config.json"
    local config_example="$SCRIPT_DIR/intelbras/data/config.example.json"
    if [ ! -f "$config_file" ] && [ -f "$config_example" ]; then
        cp "$config_example" "$config_file"
        ok "Created data/config.json from template"
        info "Edit intelbras/data/config.json to configure your cameras"
    elif [ -f "$config_file" ]; then
        ok "data/config.json exists"
    fi

    read -p "  Set up Intelbras credentials now? [y/N] " yn
    if [ "${yn,,}" = "y" ]; then
        read -p "  Alarm host IP [192.168.1.100]: " alarm_host
        read -p "  Alarm port [80]: " alarm_port
        read -p "  Alarm username [admin]: " alarm_user
        read -sp "  Alarm password: " alarm_pass && echo
        read -p "  DVR host IP [192.168.1.200]: " dvr_host
        read -p "  DVR port [80]: " dvr_port
        read -p "  DVR RTSP port [554]: " dvr_rtsp
        read -p "  DVR username [admin]: " dvr_user
        read -sp "  DVR password: " dvr_pass && echo

        save_env "INTELBRAS_ALARM_HOST" "${alarm_host:-192.168.1.100}"
        save_env "INTELBRAS_ALARM_PORT" "${alarm_port:-80}"
        save_env "INTELBRAS_ALARM_USERNAME" "${alarm_user:-admin}"
        save_env "INTELBRAS_ALARM_PASSWORD" "$alarm_pass"
        save_env "INTELBRAS_ALARM_ENABLED" "true"
        save_env "INTELBRAS_DVR_HOST" "${dvr_host:-192.168.1.200}"
        save_env "INTELBRAS_DVR_PORT" "${dvr_port:-80}"
        save_env "INTELBRAS_DVR_RTSP_PORT" "${dvr_rtsp:-554}"
        save_env "INTELBRAS_DVR_USERNAME" "${dvr_user:-admin}"
        save_env "INTELBRAS_DVR_PASSWORD" "$dvr_pass"
    else
        warn "Skipped — run ./setup.sh intelbras later to configure"
    fi
}

setup_notes_review() {
    header "notes-review"
    check_bin python3 || return 1

    info "Smoke test: review help..."
    if python3 "$SCRIPT_DIR/notes-review/scripts/review.py" --help &>/dev/null; then
        ok "notes-review works"
    else
        fail "notes-review smoke test failed"
        return 1
    fi

    if command -v qmd &>/dev/null; then
        ok "qmd found: $(command -v qmd)"
    else
        warn "qmd not found (recommended for open-ended semantic note queries)"
        info "Run: ./setup.sh qmd"
    fi
}

setup_openai_whisper() {
    header "openai-whisper"
    if ! check_bin whisper; then
        if [[ "$(uname)" == "Darwin" ]]; then
            info "Install with: brew install openai-whisper"
        else
            info "Install with: pip install openai-whisper"
        fi
        read -p "  Install now? [y/N] " yn
        if [ "${yn,,}" = "y" ]; then
            if [[ "$(uname)" == "Darwin" ]]; then
                brew install openai-whisper
            else
                pip install openai-whisper
            fi
            check_bin whisper || return 1
        else
            return 1
        fi
    fi
    ok "openai-whisper ready"
}

setup_qmd() {
    header "qmd"
    if ! check_bin qmd; then
        check_bin bun || { info "bun is required to install qmd"; return 1; }
        info "Install with: bun install -g https://github.com/tobi/qmd"
        read -p "  Install now? [y/N] " yn
        if [ "${yn,,}" = "y" ]; then
            bun install -g https://github.com/tobi/qmd
            check_bin qmd || return 1
        else
            return 1
        fi
    fi

    info "Smoke test: checking status..."
    if qmd collection list &>/dev/null; then
        ok "qmd works"
        info "Collections:"
        qmd collection list 2>/dev/null | sed 's/^/    /'
    else
        warn "qmd installed but no collections configured yet"
        info "Add one with: qmd collection add /path/to/notes --name mynotes --mask '**/*.md'"
    fi
}

setup_things3() {
    header "things3"
    if [[ "$(uname)" != "Darwin" ]]; then
        fail "macOS only — skipping on $(uname)"
        return 1
    fi

    if ! check_bin things; then
        check_bin go || { fail "go is required to install things CLI"; return 1; }
        info "Install with: GOBIN=/opt/homebrew/bin go install github.com/ossianhempel/things3-cli/cmd/things@latest"
        read -p "  Install now? [y/N] " yn
        if [ "${yn,,}" = "y" ]; then
            GOBIN=/opt/homebrew/bin go install github.com/ossianhempel/things3-cli/cmd/things@latest
            check_bin things || return 1
        else
            return 1
        fi
    fi

    info "Smoke test: listing inbox..."
    if things inbox --limit 1 &>/dev/null; then
        ok "things3 works"
    else
        warn "things CLI installed but could not read DB"
        info "Grant Full Disk Access to your terminal app"
    fi
}

setup_tmux() {
    header "tmux"
    if ! check_bin tmux; then
        if [[ "$(uname)" == "Darwin" ]]; then
            info "Install with: brew install tmux"
        else
            info "Install with: apt install tmux"
        fi
        read -p "  Install now? [y/N] " yn
        if [ "${yn,,}" = "y" ]; then
            if [[ "$(uname)" == "Darwin" ]]; then
                brew install tmux
            else
                sudo apt install -y tmux
            fi
            check_bin tmux || return 1
        else
            return 1
        fi
    fi
    ok "tmux ready"
}

setup_x_twitter_chrome() {
    header "x-twitter-chrome"
    check_bin bun || return 1

    info "Checking Chrome debug port 18800..."
    if curl -s http://127.0.0.1:18800/json &>/dev/null; then
        ok "Chrome is running on port 18800"
    else
        warn "Chrome is not running on debug port 18800"
        info "Start with:"
        if [[ "$(uname)" == "Darwin" ]]; then
            info '  /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \'
            info '    --user-data-dir="$HOME/.claude/browser/<profile>/user-data" \'
            info '    --remote-debugging-port=18800'
        else
            info '  google-chrome --user-data-dir="$HOME/.claude/browser/<profile>/user-data" --remote-debugging-port=18800'
        fi
    fi
}

# ── Main ────────────────────────────────────────────────────────

SKILLS=(
    apple-calendar
    beancount-analytics
    binance-prices
    bird
    camsnap
    elevenlabs-voices
    github
    github-secrets
    intelbras
    notes-review
    openai-whisper
    qmd
    things3
    tmux
    x-twitter-chrome
)

run_skill_setup() {
    local skill="$1"
    case "$skill" in
        apple-calendar)      setup_apple_calendar ;;
        beancount-analytics) setup_beancount_analytics ;;
        binance-prices)      setup_binance_prices ;;
        bird)                setup_bird ;;
        camsnap)             setup_camsnap ;;
        elevenlabs-voices)   setup_elevenlabs_voices ;;
        github)              setup_github ;;
        github-secrets)      setup_github_secrets ;;
        intelbras)           setup_intelbras ;;
        notes-review)        setup_notes_review ;;
        openai-whisper)      setup_openai_whisper ;;
        qmd)                 setup_qmd ;;
        things3)             setup_things3 ;;
        tmux)                setup_tmux ;;
        x-twitter-chrome)    setup_x_twitter_chrome ;;
        daily-plan|skill-creator)
            header "$skill"
            ok "Documentation-only skill — no setup needed"
            ;;
        *)
            fail "Unknown skill: $skill"
            return 1
            ;;
    esac
}

show_menu() {
    echo ""
    echo -e "${BOLD}Skills Setup${NC}"
    echo ""
    echo "Available skills:"
    echo ""
    for i in "${!SKILLS[@]}"; do
        printf "  %2d) %s\n" $((i + 1)) "${SKILLS[$i]}"
    done
    echo ""
    echo "   a) Set up all skills"
    echo "   q) Quit"
    echo ""
    read -p "Select skills (comma-separated numbers, 'a' for all, or 'q'): " selection

    if [ "$selection" = "q" ]; then
        exit 0
    elif [ "$selection" = "a" ]; then
        for skill in "${SKILLS[@]}"; do
            run_skill_setup "$skill" || true
        done
    else
        IFS=',' read -ra indices <<< "$selection"
        for idx in "${indices[@]}"; do
            idx=$(echo "$idx" | tr -d ' ')
            if [[ "$idx" =~ ^[0-9]+$ ]] && [ "$idx" -ge 1 ] && [ "$idx" -le "${#SKILLS[@]}" ]; then
                run_skill_setup "${SKILLS[$((idx - 1))]}" || true
            else
                fail "Invalid selection: $idx"
            fi
        done
    fi
}

# Entry point
if [ -n "$1" ]; then
    # Single skill mode
    run_skill_setup "$1"
else
    # Interactive menu
    show_menu
fi

echo ""
if [ -f "$ENV_FILE" ] && [ -s "$ENV_FILE" ]; then
    echo -e "${BOLD}Environment variables saved to:${NC} .env (gitignored)"
    echo -e "Load them with:"
    echo -e "  source $ENV_FILE"
    echo ""
    echo -e "Or add to your shell profile:"
    echo -e "  echo 'source $ENV_FILE' >> ~/.zshrc"
fi
echo ""
echo -e "${GREEN}Done.${NC}"
