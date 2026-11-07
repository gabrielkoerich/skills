---
name: elevenlabs-voices
version: 2.0.4
description: High-quality voice synthesis with 18 personas, 32 languages, sound effects, batch processing, and voice design using ElevenLabs API.
tags: [tts, voice, speech, elevenlabs, audio, sound-effects, voice-design, multilingual]
---

# ElevenLabs Voice Personas v2.0

Voice synthesis scripts for the ElevenLabs API.

## Features

- 18 voice personas, each picked for a use case
- 32 languages with the multilingual v2 model
- Streaming: audio plays while it generates
- Sound effects (SFX) generated from text prompts
- Batch processing of many texts in one run
- Cost tracking of character usage and estimated cost
- Voice design: create custom voices from descriptions
- Pronunciation dictionary with custom rules per word
- Works with the built-in TTS of any AI agent

## Available voices

| Voice | Accent | Gender | Persona | Best For |
|-------|--------|--------|---------|----------|
| rachel | 🇺🇸 US | female | warm | Conversations, tutorials |
| adam | 🇺🇸 US | male | narrator | Documentaries, audiobooks |
| bella | 🇺🇸 US | female | professional | Business, presentations |
| brian | 🇺🇸 US | male | comforting | Meditation, calm content |
| george | 🇬🇧 UK | male | storyteller | Audiobooks, storytelling |
| alice | 🇬🇧 UK | female | educator | Tutorials, explanations |
| callum | 🇺🇸 US | male | trickster | Playful, gaming |
| charlie | 🇦🇺 AU | male | energetic | Sports, motivation |
| jessica | 🇺🇸 US | female | playful | Social media, casual |
| lily | 🇬🇧 UK | female | actress | Drama, elegant content |
| matilda | 🇺🇸 US | female | professional | Corporate, news |
| river | 🇺🇸 US | neutral | neutral | Inclusive, informative |
| roger | 🇺🇸 US | male | casual | Podcasts, relaxed |
| daniel | 🇬🇧 UK | male | broadcaster | News, announcements |
| eric | 🇺🇸 US | male | trustworthy | Business, corporate |
| chris | 🇺🇸 US | male | friendly | Tutorials, approachable |
| will | 🇺🇸 US | male | optimist | Motivation, uplifting |
| liam | 🇺🇸 US | male | social | YouTube, social media |

## Presets

- `default` → rachel (warm, friendly)
- `narrator` → adam (documentaries)
- `professional` → matilda (corporate)
- `storyteller` → george (audiobooks)
- `educator` → alice (tutorials)
- `calm` → brian (meditation)
- `energetic` → liam (social media)
- `trustworthy` → eric (business)
- `neutral` → river (inclusive)
- `british` → george
- `australian` → charlie
- `broadcaster` → daniel (news)

## Supported languages (32)

The multilingual v2 model supports these languages:

| Code | Language | Code | Language |
|------|----------|------|----------|
| en | English | pl | Polish |
| de | German | nl | Dutch |
| es | Spanish | sv | Swedish |
| fr | French | da | Danish |
| it | Italian | fi | Finnish |
| pt | Portuguese | no | Norwegian |
| ru | Russian | tr | Turkish |
| uk | Ukrainian | cs | Czech |
| ja | Japanese | sk | Slovak |
| ko | Korean | hu | Hungarian |
| zh | Chinese | ro | Romanian |
| ar | Arabic | bg | Bulgarian |
| hi | Hindi | hr | Croatian |
| ta | Tamil | el | Greek |
| id | Indonesian | ms | Malay |
| vi | Vietnamese | th | Thai |

```bash
# Synthesize in German
python3 tts.py --text "Guten Tag!" --voice rachel --lang de

# Synthesize in French
python3 tts.py --text "Bonjour le monde!" --voice adam --lang fr

# List all languages
python3 tts.py --languages
```

## CLI usage

### Text to speech

```bash
# List all voices
python3 scripts/tts.py --list

# Generate speech
python3 scripts/tts.py --text "Hello world" --voice rachel --output hello.mp3

# Use a preset
python3 scripts/tts.py --text "Breaking news..." --voice broadcaster --output news.mp3

# Multi-language
python3 scripts/tts.py --text "Bonjour!" --voice rachel --lang fr --output french.mp3
```

### Streaming mode

Streaming plays audio while it generates. Use it for long texts:

```bash
# Stream audio as it generates
python3 scripts/tts.py --text "This is a long story..." --voice adam --stream

# Streaming with custom output
python3 scripts/tts.py --text "Chapter one..." --voice george --stream --output chapter1.mp3
```

### Batch processing

Process many texts from one file:

```bash
# From newline-separated text file
python3 scripts/tts.py --batch texts.txt --voice rachel --output-dir ./audio

# From JSON file
python3 scripts/tts.py --batch batch.json --output-dir ./output
```

JSON batch format:
```json
[
  {"text": "First line", "voice": "rachel", "output": "line1.mp3"},
  {"text": "Second line", "voice": "adam", "output": "line2.mp3"},
  {"text": "Third line"}
]
```

Text format, one text per line:
```
Hello, this is the first sentence.
This is the second sentence.
And this is the third.
```

### Usage statistics

```bash
# Show usage stats and cost estimates
python3 scripts/tts.py --stats

# Reset statistics
python3 scripts/tts.py --reset-stats
```

## Sound effects (SFX)

Generate sound effects from text descriptions:

```bash
# Generate a sound effect
python3 scripts/sfx.py --prompt "Thunder rumbling in the distance"

# With specific duration (0.5-22 seconds)
python3 scripts/sfx.py --prompt "Cat meowing" --duration 3 --output cat.mp3

# Adjust prompt influence (0.0-1.0)
python3 scripts/sfx.py --prompt "Footsteps on gravel" --influence 0.5

# Batch SFX generation
python3 scripts/sfx.py --batch sounds.json --output-dir ./sfx

# Show prompt examples
python3 scripts/sfx.py --examples
```

Example prompts:
- "Thunder rumbling in the distance"
- "Cat purring contentedly"
- "Typing on a mechanical keyboard"
- "Spaceship engine humming"
- "Coffee shop background chatter"

## Voice design

Create custom voices from text descriptions:

```bash
# Basic voice design
python3 scripts/voice-design.py --gender female --age middle_aged --accent american \
  --description "A warm, motherly voice"

# With custom preview text
python3 scripts/voice-design.py --gender male --age young --accent british \
  --text "Welcome to the adventure!" --output preview.mp3

# Save to your ElevenLabs library
python3 scripts/voice-design.py --gender female --age young --accent american \
  --description "Energetic podcast host" --save "MyHost"

# List all design options
python3 scripts/voice-design.py --options
```

Voice design options:

| Option | Values |
|--------|--------|
| Gender | male, female, neutral |
| Age | young, middle_aged, old |
| Accent | american, british, african, australian, indian, latin, middle_eastern, scandinavian, eastern_european |
| Accent Strength | 0.3-2.0 (subtle to strong) |

## Pronunciation dictionary

Set how words are pronounced in `pronunciations.json`:
```json
{
  "rules": [
    {
      "word": "Claude",
      "replacement": "Claud",
      "comment": "Pronounce correctly"
    },
    {
      "word": "API",
      "replacement": "A P I",
      "comment": "Spell out acronym"
    }
  ]
}
```

Usage:
```bash
# Pronunciations are applied automatically
python3 scripts/tts.py --text "The Claude API is great" --voice rachel

# Disable pronunciations
python3 scripts/tts.py --text "The API is great" --voice rachel --no-pronunciations
```

## Cost tracking

The scripts track character usage and estimate costs:

```bash
python3 scripts/tts.py --stats
```

Output:
```
📊 ElevenLabs Usage Statistics

  Total Characters: 15,230
  Total Requests:   42
  Since:            2024-01-15

💰 Estimated Costs:
  Starter    $4.57 ($0.30/1k chars)
  Creator    $3.66 ($0.24/1k chars)
  Pro        $2.74 ($0.18/1k chars)
  Scale      $1.68 ($0.11/1k chars)
```

## Agent TTS integration

### Agent built-in TTS

An agent with TTS support can use ElevenLabs. Configure it in `~/.claude/claude.json`:

```json
{
  "tts": {
    "enabled": true,
    "provider": "elevenlabs",
    "elevenlabs": {
      "apiKey": "your-api-key-here",
      "voice": "rachel",
      "model": "eleven_multilingual_v2"
    }
  }
}
```

### TTS in chat

In an agent conversation:
- `/tts on` turns on automatic TTS
- The `tts` tool speaks one message
- "read this aloud" or "speak this" also trigger speech

### Skill scripts from an agent

```bash
# An agent can run these scripts directly
exec python3 /path/to/skills/elevenlabs-voices/scripts/tts.py --text "Hello" --voice rachel
```

## Configuration

The scripts look for the API key in this order:

1. `ELEVEN_API_KEY` or `ELEVENLABS_API_KEY` environment variable
2. Agent config (`~/.claude/claude.json` → tts.elevenlabs.apiKey)
3. Skill-local `.env` file

Create the `.env` file:
```bash
echo 'ELEVEN_API_KEY=your-key-here' > .env
```

## Voice settings

Each voice has its own tuned settings:

| Setting | Range | Description |
|---------|-------|-------------|
| stability | 0.0-1.0 | Higher = consistent, lower = expressive |
| similarity_boost | 0.0-1.0 | How closely to match original voice |
| style | 0.0-1.0 | Exaggeration of speaking style |

## Triggers

- "use {voice_name} voice"
- "speak as {persona}"
- "list voices"
- "voice settings"
- "generate sound effect"
- "design a voice"

## Files

```
elevenlabs-voices/
├── SKILL.md              # This documentation
├── README.md             # Quick start guide
├── voices.json           # Voice definitions & settings
├── pronunciations.json   # Custom pronunciation rules
├── examples.md           # Detailed usage examples
├── scripts/
│   ├── tts.py            # Main TTS script
│   ├── sfx.py            # Sound effects generator
│   └── voice-design.py   # Voice design tool
└── references/
    └── voice-guide.md    # Voice selection guide
```

## Links

- [ElevenLabs](https://elevenlabs.io)
- [API Documentation](https://docs.elevenlabs.io)
- [Voice Library](https://elevenlabs.io/voice-library)
- [Sound Effects API](https://elevenlabs.io/docs/api-reference/sound-generation)
- [Voice Design API](https://elevenlabs.io/docs/api-reference/voice-generation)

## Changelog

### v2.0.0
- Added 32 language support with `--lang` parameter
- Added streaming mode with `--stream` flag
- Added sound effects generation (`sfx.py`)
- Added batch processing with `--batch` flag
- Added cost tracking with `--stats` flag
- Added voice design tool (`voice-design.py`)
- Added pronunciation dictionary support
- Added agent TTS integration documentation
- Improved error handling and progress output
