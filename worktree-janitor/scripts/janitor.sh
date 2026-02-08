#!/usr/bin/env bash
set -euo pipefail
cmd="${1:-audit}"
arg="${2:-}"

case "$cmd" in
  list)
    git worktree list
    ;;
  audit)
    echo "[worktrees]"
    git worktree list
    echo
    echo "[merged local branches]"
    git branch --merged | sed 's/^..//'
    ;;
  remove)
    if [[ -z "$arg" ]]; then
      echo "usage: $0 remove <path>" >&2
      exit 2
    fi
    git worktree remove "$arg"
    ;;
  prune)
    git worktree prune
    ;;
  *)
    echo "usage: $0 {list|audit|remove|prune} [path]" >&2
    exit 2
    ;;
esac
