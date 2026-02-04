#!/bin/bash
# GitHub Secrets helper script
# Common operations for managing secrets

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check token
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}Error: GITHUB_TOKEN is not set${NC}"
    echo "Set it with: export GITHUB_TOKEN='ghp_your_token'"
    exit 1
fi

show_help() {
    cat << EOF
GitHub Secrets Helper

Usage: ./scripts/secrets.sh <command> [options]

Commands:
    list <owner> <repo>         List repository secrets
    list-org <org>              List organization secrets
    set <owner> <repo> <name>    Set a secret (prompts for value)
    delete <owner> <repo> <name> Delete a secret
    sync <owner> <repo> <file>   Sync secrets from JSON file
    backup <owner> <repo>        Backup secrets to JSON (names only)
    copy <src> <dst>            Copy secrets between repos (src/dst = owner/repo)

Examples:
    ./scripts/secrets.sh list myuser myrepo
    ./scripts/secrets.sh set myuser myrepo API_KEY
    ./scripts/secrets.sh sync myuser myrepo secrets.json
    ./scripts/secrets.sh copy myuser/oldrepo myuser/newrepo
EOF
}

list_secrets() {
    local owner=$1
    local repo=$2
    echo -e "${YELLOW}Listing secrets for $owner/$repo...${NC}"
    bun run list --owner "$owner" --repo "$repo"
}

list_org_secrets() {
    local org=$1
    echo -e "${YELLOW}Listing secrets for organization $org...${NC}"
    bun run list --org "$org"
}

set_secret() {
    local owner=$1
    local repo=$2
    local name=$3
    
    echo -n "Enter value for $name: "
    read -s value
    echo
    
    echo -e "${YELLOW}Setting secret $name...${NC}"
    bun run set --owner "$owner" --repo "$repo" --name "$name" --value "$value"
    echo -e "${GREEN}✅ Secret set successfully${NC}"
}

delete_secret() {
    local owner=$1
    local repo=$2
    local name=$3
    
    echo -e "${YELLOW}Deleting secret $name from $owner/$repo...${NC}"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        bun run delete --owner "$owner" --repo "$repo" --name "$name" --force
        echo -e "${GREEN}✅ Secret deleted${NC}"
    else
        echo "Cancelled."
    fi
}

sync_secrets() {
    local owner=$1
    local repo=$2
    local file=$3
    
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: File $file not found${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Syncing secrets from $file to $owner/$repo...${NC}"
    
    # Dry run first
    echo -e "${YELLOW}Previewing changes...${NC}"
    bun run sync --owner "$owner" --repo "$repo" --file "$file" --dry-run
    
    echo
    read -p "Apply these changes? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        bun run sync --owner "$owner" --repo "$repo" --file "$file"
        echo -e "${GREEN}✅ Sync complete${NC}"
    else
        echo "Cancelled."
    fi
}

backup_secrets() {
    local owner=$1
    local repo=$2
    local output="${owner}_${repo}_secrets_backup_$(date +%Y%m%d).json"
    
    echo -e "${YELLOW}Backing up secrets from $owner/$repo...${NC}"
    bun run list --owner "$owner" --repo "$repo" --json > "$output"
    echo -e "${GREEN}✅ Backup saved to $output${NC}"
}

copy_secrets() {
    local src=$1
    local dst=$2
    
    local src_owner=$(echo "$src" | cut -d'/' -f1)
    local src_repo=$(echo "$src" | cut -d'/' -f2)
    local dst_owner=$(echo "$dst" | cut -d'/' -f1)
    local dst_repo=$(echo "$dst" | cut -d'/' -f2)
    
    echo -e "${YELLOW}Copying secrets from $src to $dst...${NC}"
    
    # Get source secrets
    local backup_file="temp_backup_$(date +%s).json"
    bun run list --owner "$src_owner" --repo "$src_repo" --json > "$backup_file"
    
    echo -e "${YELLOW}Found $(cat "$backup_file" | grep -c '"name"' || echo 0) secrets${NC}"
    echo -e "${RED}Note: Secret values cannot be copied (GitHub API limitation)${NC}"
    echo "You'll need to manually set values for each secret."
    
    rm "$backup_file"
}

# Main
case "${1:-}" in
    list)
        [ -z "$2" ] || [ -z "$3" ] && { echo "Usage: list <owner> <repo>"; exit 1; }
        list_secrets "$2" "$3"
        ;;
    list-org)
        [ -z "$2" ] && { echo "Usage: list-org <org>"; exit 1; }
        list_org_secrets "$2"
        ;;
    set)
        [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] && { echo "Usage: set <owner> <repo> <name>"; exit 1; }
        set_secret "$2" "$3" "$4"
        ;;
    delete)
        [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] && { echo "Usage: delete <owner> <repo> <name>"; exit 1; }
        delete_secret "$2" "$3" "$4"
        ;;
    sync)
        [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] && { echo "Usage: sync <owner> <repo> <file>"; exit 1; }
        sync_secrets "$2" "$3" "$4"
        ;;
    backup)
        [ -z "$2" ] || [ -z "$3" ] && { echo "Usage: backup <owner> <repo>"; exit 1; }
        backup_secrets "$2" "$3"
        ;;
    copy)
        [ -z "$2" ] || [ -z "$3" ] && { echo "Usage: copy <owner/repo> <owner/repo>"; exit 1; }
        copy_secrets "$2" "$3"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: ${1:-none}${NC}"
        show_help
        exit 1
        ;;
esac
