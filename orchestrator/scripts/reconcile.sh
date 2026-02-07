#!/usr/bin/env bash
set -euo pipefail

ORCH_BIN="${ORCHESTRATOR_BIN:-orchestrator}"

if ! command -v "$ORCH_BIN" >/dev/null 2>&1; then
  echo "error: orchestrator binary not found on PATH: $ORCH_BIN" >&2
  exit 1
fi

if [ "$#" -eq 0 ]; then
  set -- gh-sync
fi

echo "Running: $ORCH_BIN $*"
exec "$ORCH_BIN" "$@"
