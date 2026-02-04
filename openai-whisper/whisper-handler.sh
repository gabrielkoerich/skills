#!/bin/bash
# Whisper STT integration for Claude
# Usage: ./whisper-handler.sh <audio_file> [output_format]

set -e

AUDIO_FILE="${1:-}"
OUTPUT_FORMAT="${2:-txt}"
OUTPUT_DIR="${3:-/tmp}"

if [ -z "$AUDIO_FILE" ]; then
    echo "Usage: $0 <audio_file> [output_format] [output_dir]"
    exit 1
fi

if [ ! -f "$AUDIO_FILE" ]; then
    echo "Error: Audio file not found: $AUDIO_FILE"
    exit 1
fi

# Transcribe using Whisper
whisper "$AUDIO_FILE" \
    --model turbo \
    --output_format "$OUTPUT_FORMAT" \
    --output_dir "$OUTPUT_DIR" \
    --language English \
    2>&1 | grep -v "^whisper:"

# Output file path (same name, different extension)
BASENAME=$(basename "$AUDIO_FILE" | sed 's/\.[^.]*$//')
OUTPUT_FILE="${OUTPUT_DIR}/${BASENAME}.${OUTPUT_FORMAT}"

if [ -f "$OUTPUT_FILE" ]; then
    echo "Transcription saved to: $OUTPUT_FILE"
    cat "$OUTPUT_FILE"
else
    echo "Error: Transcription failed"
    exit 1
fi
