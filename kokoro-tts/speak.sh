#!/usr/bin/env bash
# Kokoro TTS via mlx-audio, runs on the Metal GPU, no network after first run
# Usage: speak.sh "text" [-v voice] [-o out.wav] [-s speed] [--play]
set -euo pipefail

VENV="$HOME/.local/share/kokoro-tts/.venv"
MODEL="mlx-community/Kokoro-82M-bf16"
BIN="$VENV/bin/mlx_audio.tts.generate"

[ -x "$BIN" ] || { echo "kokoro-tts env missing, see SKILL.md setup" >&2; exit 1; }

text="" voice="af_heart" out="" speed="1.0" play=0
while [ $# -gt 0 ]; do
  case "$1" in
    -v|--voice) voice="$2"; shift 2 ;;
    -o|--out)   out="$2"; shift 2 ;;
    -s|--speed) speed="$2"; shift 2 ;;
    --play)     play=1; shift ;;
    *)          text="$1"; shift ;;
  esac
done

# Read stdin when no text argument is given
[ -n "$text" ] || text="$(cat)"
[ -n "$text" ] || { echo "no text given" >&2; exit 1; }

out="${out:-$(mktemp -t kokoro).wav}"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

# lang_code comes from the voice prefix, Kokoro mispronounces without it
case "$voice" in
  a*) lang=a ;; b*) lang=b ;; e*) lang=e ;; f*) lang=f ;; h*) lang=h ;;
  i*) lang=i ;; j*) lang=j ;; p*) lang=p ;; z*) lang=z ;; *) lang=a ;;
esac

(cd "$tmpdir" && "$BIN" --model "$MODEL" --text "$text" --voice "$voice" \
  --speed "$speed" --lang_code "$lang" --file_prefix seg --audio_format wav \
  --join_audio >/dev/null 2>&1)

# --join_audio writes seg.wav, otherwise one seg_NNN.wav per chunk
if [ -f "$tmpdir/seg.wav" ]; then
  mv "$tmpdir/seg.wav" "$out"
else
  segs=("$tmpdir"/seg_*.wav)
  [ -e "${segs[0]}" ] || { echo "synthesis produced no audio" >&2; exit 1; }
  if [ "${#segs[@]}" -eq 1 ]; then
    mv "${segs[0]}" "$out"
  else
    printf "file '%s'\n" "${segs[@]}" > "$tmpdir/list"
    ffmpeg -nostdin -loglevel error -f concat -safe 0 -i "$tmpdir/list" -c copy "$out" -y
  fi
fi

echo "$out"
if [ "$play" -eq 1 ]; then afplay "$out"; fi
