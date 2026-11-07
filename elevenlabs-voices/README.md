# ElevenLabs Voice Personas v2.0.0

Voice synthesis with the ElevenLabs API: 18 personas, 32 languages, sound effects and voice design.

## Quick start

```bash
# Set your API key
export ELEVEN_API_KEY="your-key-here"

# Basic TTS
python3 scripts/tts.py --text "Hello world" --voice rachel

# Multi-language
python3 scripts/tts.py --text "Bonjour!" --voice rachel --lang fr

# Sound effects
python3 scripts/sfx.py --prompt "Thunder rumbling"

# Batch processing
python3 scripts/tts.py --batch texts.txt --voice adam --output-dir ./audio

# Usage stats
python3 scripts/tts.py --stats
```

## Features

| Feature | Command |
|---------|---------|
| TTS | `python3 scripts/tts.py --text "..." --voice NAME` |
| Languages (32) | `--lang de` (German), `--lang fr` (French), etc. |
| Streaming | `--stream` |
| Batch | `--batch file.txt --output-dir ./out` |
| Sound Effects | `python3 scripts/sfx.py --prompt "..."` |
| Voice Design | `python3 scripts/voice-design.py --gender female --age young` |
| Cost Stats | `--stats` |

## Voice presets

- `narrator`: documentary style
- `storyteller`: audiobooks
- `professional`: corporate
- `educator`: tutorials
- `calm`: meditation
- `energetic`: social media
- `broadcaster`: news

## Documentation

- [SKILL.md](SKILL.md): full documentation
- [examples.md](examples.md): usage examples
- [voices.json](voices.json): voice configurations
- [pronunciations.json](pronunciations.json): custom pronunciations

## License

MIT. API usage follows the ElevenLabs terms.
