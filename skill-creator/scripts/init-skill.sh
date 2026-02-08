#!/usr/bin/env bash
set -euo pipefail
NAME="${1:-}"
DESC="${2:-}"

if [[ -z "$NAME" || -z "$DESC" ]]; then
  echo "usage: $0 <skill-name> <description>" >&2
  exit 2
fi

ROOT="$(pwd)/$NAME"
mkdir -p "$ROOT/scripts" "$ROOT/agents"

cat > "$ROOT/SKILL.md" <<MD
---
name: $NAME
description: $DESC
---

# $NAME

Describe workflow and commands.
MD

cat > "$ROOT/agents/openai.yaml" <<YAML
version: 1
display_name: $NAME
short_description: $DESC
default_prompt: Use this skill for $DESC
YAML

echo "created $ROOT"
