#!/usr/bin/env bash
set -euo pipefail
BASE_BRANCH="${1:-main}"

git fetch origin "$BASE_BRANCH" >/dev/null

TITLE="feat: $(git rev-parse --abbrev-ref HEAD | sed 's#^.*/##')"
SUMMARY="$(git log --no-merges --pretty='- %s' "origin/$BASE_BRANCH..HEAD")"
FILES="$(git diff --name-only "origin/$BASE_BRANCH..HEAD" | sed 's/^/- /')"

cat <<PR
TITLE=$TITLE

## Summary

${SUMMARY:-- Update implementation}

## Changed Files

${FILES:-- No file list available}

## Testing

- [ ] Add testing notes
PR
