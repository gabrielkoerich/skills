---
name: macos-say
description: Free offline text-to-speech on macOS with the built-in `say` command. Speak text aloud, narrate a file, or render speech to wav/m4a/aiff using system voices. No API key, no network, no cost. Use when asked to speak, read aloud, narrate, voice, or generate TTS audio.
tags: [tts, speech, voice, audio, macos, offline, free]
---

# macOS `say` (offline TTS)

`/usr/bin/say` ships with macOS. It runs on-device, costs nothing, and needs no key.

## When not to use this

The compact voices sound dated. For natural quality use the `kokoro-tts` skill instead,
which runs Kokoro-82M on the Metal GPU. Stay here when you need zero startup latency.

## Speak aloud

```bash
say "Build finished, seven tests passed"
say -v Samantha "Build finished"
say -r 210 "Read this faster"              # words per minute, default ~175
```

Ask before playing audio if the user did not request sound. It plays through their speakers.

## Render to a file

```bash
say -o out.aiff "Hello"                     # AIFF, always supported
say -o out.wav --data-format=LEI16@22050 "Hello"   # 16-bit PCM wav
say -o out.m4a --data-format=aac --bit-rate=64000 "Hello"  # small, for sharing
afplay out.wav                              # play a rendered file
```

The file format comes from the extension. `--data-format` controls the samples.
Use `say --file-format=?` and `say -o x.wav --data-format=?` to list what a format accepts.

## Long text

```bash
say -f script.txt                           # narrate a file
say -f script.txt -o narration.m4a --data-format=aac
pbpaste | say                               # speak the clipboard
```

Read from a file, not a terminal. When stdin is a TTY, `say` speaks line by line and
an `-o` file keeps only the last line.

## Voices

```bash
say -v '?'                                  # all installed voices
say -v '?' | grep en_                       # English only
~/.claude/skills/macos-say/voices.sh        # narration voices, novelty ones filtered out
```

Quote names that contain spaces or parentheses: `say -v "Eddy (English (UK))" "hi"`.

Decent defaults for narration: `Samantha` (en_US), `Daniel` (en_GB), `Karen` (en_AU),
`Moira` (en_IE), `Tessa` (en_ZA). Skip `Bad News`, `Bells`, `Boing`, `Bubbles`,
`Cellos`, `Jester`, `Organ`, `Trinoids`, `Whisper`, `Zarvox` and friends. They are
novelty voices and sound like a 1996 startup chime.

### Getting better quality

The default voices are the *compact* ones and sound dated. Apple ships neural
Enhanced and Premium voices as a free download:

**System Settings > Accessibility > Spoken Content > System Voice > Manage Voices**

Download a Premium voice, then call it by its full display name:

```bash
say -v "Zoe (Premium)" "This is the neural voice"
```

The quality jump is large and it is the single highest-value thing to do here.
Siri voices are not reachable from `say` or any public API.

## Inline speech controls

Plain text accepts markup:

```bash
say "First point [[slnc 500]] second point"    # 500 ms pause
say "This is [[emph +]]important[[emph -]]"    # emphasis
say "[[rate 140]]Slow down for this part"
```

## Gotchas

- Text starting with `-` needs `--` first: `say -- "-5 degrees"`.
- `say` returns non-zero on failure, so `set -e` scripts catch it.
- A very long single `say` call blocks until done. Render to a file for long text.
- Voices are per-user downloads but visible to every logged-in user on the Mac.
