#!/usr/bin/env bash
# Lists say(1) voices worth using for narration, novelty voices filtered out
# Usage: voices.sh [locale-substring]   e.g. voices.sh en_
set -euo pipefail

filter="${1:-}"

novelty="Albert|Bad News|Bahh|Bells|Boing|Bruce|Bubbles|Cellos|Deranged|Fred|Good News|Hysterical|Jester|Junior|Kathy|Organ|Pipe Organ|Princess|Ralph|Superstar|Trinoids|Whisper|Wobble|Zarvox"

parsed=$(say -v '?' \
  | sed -E 's/^(.*[^ ]) +([a-z]{2}[-_][A-Za-z]+) +#.*/\2\t\1/' \
  | grep -Ev "\t($novelty)$" \
  | sort)

if [ -n "$filter" ]; then
  parsed=$(printf '%s\n' "$parsed" | grep -- "$filter" || true)
fi

neural=$(printf '%s\n' "$parsed" | grep -E '\((Premium|Enhanced)\)$' || true)

if [ -n "$neural" ]; then
  echo "Neural voices (best quality):"
  printf '%s\n' "$neural" | awk -F'\t' '{printf "  %-28s %s\n", $2, $1}'
  echo
else
  echo "No Enhanced/Premium voices installed."
  echo "Get them free: System Settings > Accessibility > Spoken Content > System Voice > Manage Voices"
  echo
fi

echo "All usable voices:"
printf '%s\n' "$parsed" | awk -F'\t' '{printf "  %-28s %s\n", $2, $1}'
