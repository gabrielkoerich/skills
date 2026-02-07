#!/usr/bin/env bash
set -euo pipefail

ORCH_BIN="${ORCHESTRATOR_BIN:-orchestrator}"

if ! command -v "$ORCH_BIN" >/dev/null 2>&1; then
  echo "error: orchestrator binary not found on PATH: $ORCH_BIN" >&2
  exit 1
fi

echo "Running: $ORCH_BIN status"
"$ORCH_BIN" status

if [ "$#" -gt 0 ]; then
  echo ""
  echo "Running: $ORCH_BIN $*"
  exec "$ORCH_BIN" "$@"
fi
