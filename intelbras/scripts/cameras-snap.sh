#!/bin/bash
# Take snapshots from all cameras
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/intelbras-alarm.py" all-snap
