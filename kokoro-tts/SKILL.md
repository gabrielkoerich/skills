---
name: kokoro-tts
description: High quality offline text-to-speech with Kokoro-82M running on the Apple Silicon GPU via MLX. 54 voices, 9 languages, Apache-2.0, no API key and no cost. Use when asked to speak, narrate, read aloud, or generate natural sounding TTS audio, and when macos-say voices sound too robotic.
tags: [tts, speech, voice, audio, kokoro, mlx, metal, offline, free, local]
---

# Kokoro TTS (local, Metal GPU)

Kokoro-82M through `mlx-audio`. Runs on the Metal GPU on Apple Silicon. Apache-2.0,
so commercial use is free. Sounds close to a paid API, unlike the `say` compact voices.

Use `macos-say` instead when you need zero startup latency and do not care about quality.

## Speak

```bash
~/.claude/skills/kokoro-tts/speak.sh "Your text here" -o out.wav
~/.claude/skills/kokoro-tts/speak.sh "Your text" -v bm_george -o out.wav --play
cat script.txt | ~/.claude/skills/kokoro-tts/speak.sh -v am_michael -o narration.wav
```

| Flag | Meaning |
|------|---------|
| `-v` | voice id, default `af_heart` |
| `-o` | output wav path, default a temp file |
| `-s` | speed, 1.0 is normal |
| `--play` | play through speakers after writing |

The script prints the output path on stdout. Output is 24 kHz mono 16-bit wav.

Ask before using `--play`. It makes noise on the user's machine.

## Voices

First letter is language, second is gender. `af_heart` is the default and the
best rated. `af_bella`, `am_michael`, `bf_emma` and `bm_george` are also strong.

| Prefix | Language | Voices |
|--------|----------|--------|
| `af_` `am_` | American English | alloy, aoede, bella, heart, jessica, kore, nicole, nova, river, sarah, sky / adam, echo, eric, fenrir, liam, michael, onyx, puck, santa |
| `bf_` `bm_` | British English | alice, emma, isabella, lily / daniel, fable, george, lewis |
| `ef_` `em_` | Spanish | dora / alex, santa |
| `ff_` | French | siwis |
| `hf_` `hm_` | Hindi | alpha, beta / omega, psi |
| `if_` `im_` | Italian | sara / nicola |
| `jf_` `jm_` | Japanese | alpha, gongitsune, nezumi, tebukuro / kumo |
| `pf_` `pm_` | Brazilian Portuguese | dora / alex, santa |
| `zf_` `zm_` | Mandarin | xiaobei, xiaoni, xiaoxiao, xiaoyi / yunjian, yunxi, yunxia, yunyang |

Non-English voices past American and British English are not QA'd upstream. Check
output before shipping them.

## Performance

Roughly 5 seconds of fixed startup per call, for Python imports and model load.
Synthesis itself runs faster than real time. A 21 second clip took 8 seconds total.

For many short calls in a row, run the HTTP server once instead:

```bash
~/.local/share/kokoro-tts/.venv/bin/mlx_audio.server   # then POST to it
```

## Setup

`speak.sh` expects the venv at `~/.local/share/kokoro-tts`. Install it once:

```bash
mkdir -p ~/.local/share/kokoro-tts && cd ~/.local/share/kokoro-tts
uv venv --python 3.12
uv pip install "mlx-audio[tts]" "misaki[en]"
.venv/bin/python -m spacy download en_core_web_sm
```

Python 3.12 is required. The stack does not build on 3.14.

Three install traps, all hit during setup:

1. `mlx-audio[tts]` does not pull `misaki`, so Kokoro fails at import.
2. `misaki` alone lacks `num2words`. You need `misaki[en]`.
3. `misaki` needs the spaCy English model, which is not a PyPI dependency.

Costs 1.2 GB of venv, mostly torch pulled in by spaCy, plus the model in
`~/.cache/huggingface`. Everything is isolated. System and Homebrew Python are untouched.

Remove with `trash ~/.local/share/kokoro-tts`.
