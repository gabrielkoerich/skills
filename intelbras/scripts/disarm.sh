#!/bin/bash
# Disarm Intelbras alarm
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/intelbras-alarm.py" disarm
