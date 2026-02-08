#!/usr/bin/env bash
set -euo pipefail
BASE_BRANCH="${1:-main}"
OUT="$(scripts/make-pr-body.sh "$BASE_BRANCH")"
TITLE="$(printf '%s\n' "$OUT" | sed -n 's/^TITLE=//p' | head -n1)"
BODY="$(printf '%s\n' "$OUT" | sed '1,2d')"
HEAD="$(git rev-parse --abbrev-ref HEAD)"

gh pr create --base "$BASE_BRANCH" --head "$HEAD" --title "$TITLE" --body "$BODY"
