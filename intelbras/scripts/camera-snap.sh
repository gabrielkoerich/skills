#!/bin/bash
# Take snapshot from a camera
# Usage: ./camera-snap.sh <camera_name>
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "$1" ]; then
    echo "Usage: $0 <camera_name>"
    echo "Example: $0 BACKLEFT"
    exit 1
fi
python3 "$SCRIPT_DIR/intelbras-alarm.py" snap "$1"
