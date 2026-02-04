#!/bin/bash
# Set Intelbras alarm to partial mode
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/intelbras-alarm.py" partial
