#!/usr/bin/env bash
set -euo pipefail

FIX=0
ROOT=""

for arg in "$@"; do
  case "$arg" in
    --fix) FIX=1 ;;
    *) ROOT="$arg" ;;
  esac
done

if [[ -z "$ROOT" ]]; then
  ROOT="$(pwd)"
fi

if [[ ! -d "$ROOT" ]]; then
  echo "error: root not found: $ROOT" >&2
  exit 2
fi

overall_fail=0

for d in "$ROOT"/*; do
  [[ -d "$d" ]] || continue
  skill_md="$d/SKILL.md"
  [[ -f "$skill_md" ]] || continue

  dir_name="$(basename "$d")"
  name="$(sed -n 's/^name: //p' "$skill_md" | head -n1 | sed 's/^"//;s/"$//')"
  desc="$(sed -n 's/^description: //p' "$skill_md" | head -n1 | sed 's/^"//;s/"$//')"

  if [[ -z "$name" ]]; then
    echo "[ERR] $dir_name: missing frontmatter name"
    overall_fail=1
  fi
  if [[ -z "$desc" ]]; then
    echo "[ERR] $dir_name: missing frontmatter description"
    overall_fail=1
  fi

  if [[ -n "$name" && "$name" != "$dir_name" ]]; then
    echo "[ERR] $dir_name: name mismatch (name=$name)"
    if [[ "$FIX" -eq 1 ]]; then
      sed -i.bak "s/^name: .*/name: $dir_name/" "$skill_md" && rm -f "$skill_md.bak"
      echo "[FIX] $dir_name: updated name to $dir_name"
    else
      overall_fail=1
    fi
  fi

  # Placeholder consistency: avoid mixed project/repo placeholder usage
  has_repo=0
  has_project=0
  rg -q "<repo-name>" "$skill_md" && has_repo=1 || true
  rg -q "<project-name>" "$skill_md" && has_project=1 || true
  if [[ "$has_repo" -eq 1 && "$has_project" -eq 1 ]]; then
    echo "[ERR] $dir_name: mixed placeholders <repo-name> and <project-name>"
    if [[ "$FIX" -eq 1 ]]; then
      sed -i.bak 's/<repo-name>/<project-name>/g' "$skill_md" && rm -f "$skill_md.bak"
      echo "[FIX] $dir_name: normalized <repo-name> -> <project-name>"
    else
      overall_fail=1
    fi
  fi

  # Check for agents/openai.yaml
  openai_yaml="$d/agents/openai.yaml"
  if [[ ! -f "$openai_yaml" ]]; then
    echo "[ERR] $dir_name: missing agents/openai.yaml"
    if [[ "$FIX" -eq 1 && -n "$name" && -n "$desc" ]]; then
      display_name="$(echo "$name" | sed 's/-/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1')"
      mkdir -p "$d/agents"
      cat > "$openai_yaml" <<YAML
version: 1
display_name: "$display_name"
short_description: "$desc"
default_prompt: "Use the $name skill for this task."
YAML
      echo "[FIX] $dir_name: created agents/openai.yaml"
    else
      overall_fail=1
    fi
  fi

  # Check for .claude-plugin/plugin.json
  plugin_json="$d/.claude-plugin/plugin.json"
  if [[ ! -f "$plugin_json" ]]; then
    echo "[ERR] $dir_name: missing .claude-plugin/plugin.json"
    if [[ "$FIX" -eq 1 && -n "$name" && -n "$desc" ]]; then
      mkdir -p "$d/.claude-plugin"
      printf '{\n  "name": "%s",\n  "description": "%s"\n}\n' "$name" "$desc" > "$plugin_json"
      echo "[FIX] $dir_name: created .claude-plugin/plugin.json"
    else
      overall_fail=1
    fi
  fi
done

if [[ "$overall_fail" -ne 0 ]]; then
  exit 1
fi

echo "lint complete"
