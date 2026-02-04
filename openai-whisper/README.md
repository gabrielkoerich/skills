# OpenAI Whisper (Local STT)

Local speech-to-text using OpenAI's Whisper CLI.

## Usage

```bash
# Transcribe audio file
whisper audio.m4a --model medium --output_dir .

# Translate to English
whisper audio.mp3 --task translate

# Output as JSON
whisper audio.wav --output_format json
```

## Agent Integration

STT (Speech-to-Text) can be integrated with any AI agent.

### Configuration

STT config can be added to `~/.claude/claude.json`:

```json
{
  "messages": {
    "stt": {
      "provider": "whisper",
      "enabled": true,
      "whisper": {
        "model": "turbo",
        "language": "en"
      }
    }
  }
}
```

### Voice Command Flow

```
User sends voice message
         ▼
Agent receives audio file
         ▼
Whisper transcribes 🎙️ → Text
         ▼
Agent processes text
         ▼
Agent responds (ElevenLabs voice) 🎙️
```

### Handler Script

Use the handler script for custom integrations:

```bash
./whisper-handler.sh <audio_file> [format] [output_dir]

# Example
./whisper-handler.sh voice.m4a txt /tmp
```

## Notes

- Models download to `~/.cache/whisper` on first run
- Default model: `turbo` (fast)
- For better accuracy: `medium` or `large`
- Supported formats: mp3, wav, m4a, flac, ogg

## Installation

```bash
brew install openai-whisper
```
