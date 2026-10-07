set shell := ["bash", "-euo", "pipefail", "-c"]

repo := justfile_directory()
local_skills := env_var_or_default("SKILLS_DIR", home_directory() / ".claude/skills")
# Skill names to never sync, kept outside this public repo, one per line, `#` comments allowed
ignore_file := local_skills / ".sync-ignore"
# Extra private grep terms for the leak check (names, employers), one regex per line, kept outside the repo
leak_terms_file := local_skills / ".sync-leak-terms"
excludes := "--exclude=.DS_Store --exclude=.usage.json --exclude=node_modules --exclude=__pycache__ --exclude=.cache --exclude=.venv --exclude=[0-9]"

# Show available recipes
@default:
  just --list

# Lint all skills (check mode)
lint-skills:
  ./skill-lint/scripts/lint-skills.sh

# Lint all skills and auto-fix safe issues
lint-skills-fix:
  ./skill-lint/scripts/lint-skills.sh --fix

# Copy every repo skill into the local skills folder, never deletes local-only skills
sync-to-local:
  #!/usr/bin/env bash
  set -euo pipefail
  ignored="$(sed -e 's/#.*//' -e 's/[[:space:]]//g' "{{ignore_file}}" 2>/dev/null | grep -v '^$' || true)"
  mkdir -p "{{local_skills}}"
  for d in "{{repo}}"/*/SKILL.md; do
    s="$(basename "$(dirname "$d")")"
    if grep -qxF -- "$s" <<<"$ignored"; then echo "skip $s (in .sync-ignore)"; continue; fi
    # -u keeps a local file that is newer than the repo copy, run sync-diff to see those
    rsync -au {{excludes}} "{{repo}}/$s/" "{{local_skills}}/$s/"
    echo "synced $s"
  done

# Copy local changes back, only for skills the repo already has, then run leak checks
sync-from-local:
  #!/usr/bin/env bash
  set -euo pipefail
  ignored="$(sed -e 's/#.*//' -e 's/[[:space:]]//g' "{{ignore_file}}" 2>/dev/null | grep -v '^$' || true)"
  for s in $ignored; do
    if [ -e "{{repo}}/$s" ]; then
      echo "!!!!!!!! STOP: '$s' is in {{ignore_file}} but exists in the repo at {{repo}}/$s" >&2
      echo "!!!!!!!! A private skill may be about to go public. Remove it from the repo or from .sync-ignore first." >&2
      exit 1
    fi
  done
  changed="$(mktemp)"
  for d in "{{repo}}"/*/SKILL.md; do
    s="$(basename "$(dirname "$d")")"
    [ -d "{{local_skills}}/$s" ] || continue
    rsync -ac {{excludes}} --exclude=.claude-plugin --out-format="$s/%n" \
      "{{local_skills}}/$s/" "{{repo}}/$s/" | grep -v '/$' >>"$changed" || true
  done
  if [ ! -s "$changed" ]; then echo "nothing changed"; exit 0; fi
  echo "== changed files"; cat "$changed"
  just leak-check "$changed"
  if [ -d "{{repo}}/.git" ]; then echo "== git status"; git -C "{{repo}}" status --short; fi
  echo "Review the diff, then commit by hand."

# Grep the listed files (or the whole repo) for personal data and secrets
leak-check list="":
  #!/usr/bin/env bash
  set -uo pipefail
  cd "{{repo}}"
  if [ -n "{{list}}" ]; then files=(); while IFS= read -r f; do [ -f "$f" ] && files+=("$f"); done <"{{list}}"; else files=(.); fi
  [ ${#files[@]} -gt 0 ] || { echo "leak-check: no files"; exit 0; }
  pat='/Users/[a-z]|@gmail|192\.168\.|(^|[^0-9.])100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.[0-9]+\.[0-9]+|\.ts\.net|(api_?key|token|secret|private_?key|password)["'\'']?[[:space:]]*[:=][[:space:]]*["'\''][^"'\''$<{ ]{8,}|BEGIN [A-Z ]*PRIVATE|0x[0-9a-fA-F]{40}|[1-9A-HJ-NP-Za-km-z]{33,}|\+?[0-9]{2}[ (]*[0-9]{2}[) ]*9?[0-9]{4}[- ]?[0-9]{4}'
  echo "== leak grep"
  rg -n -i --no-heading -e "$pat" "${files[@]}" || echo "no generic hits"
  if [ -s "{{leak_terms_file}}" ]; then
    echo "== private terms from {{leak_terms_file}}"
    rg -n -i --no-heading -f "{{leak_terms_file}}" "${files[@]}" || echo "no private-term hits"
  fi
  if command -v gitleaks >/dev/null; then
    echo "== gitleaks"
    found=0
    for f in "${files[@]}"; do gitleaks detect --no-git --no-banner --log-level=warn --source "$f" || found=1; done
    [ "$found" -eq 0 ] && echo "no gitleaks findings"
  else
    echo "gitleaks not installed, skipped"
  fi

# Show which shared skills differ and which side changed last, changes nothing
sync-diff:
  #!/usr/bin/env bash
  set -euo pipefail
  ignored="$(sed -e 's/#.*//' -e 's/[[:space:]]//g' "{{ignore_file}}" 2>/dev/null | grep -v '^$' || true)"
  newest() { find "$1" -type f -not -path '*/.claude-plugin/*' -not -name .DS_Store -not -name .usage.json -exec stat -f %m {} + 2>/dev/null | sort -n | tail -1; }
  for d in "{{repo}}"/*/SKILL.md; do
    s="$(basename "$(dirname "$d")")"
    grep -qxF -- "$s" <<<"$ignored" && continue
    [ -d "{{local_skills}}/$s" ] || { echo "$s: repo only"; continue; }
    if out="$(rsync -nac {{excludes}} --exclude=.claude-plugin --out-format=%n "{{local_skills}}/$s/" "{{repo}}/$s/" | grep -v '/$')" && [ -n "$out" ]; then
      l="$(newest "{{local_skills}}/$s")"
      if [ -d "{{repo}}/.git" ]; then r="$(git -C "{{repo}}" log -1 --format=%ct -- "$s")"; else r="$(newest "{{repo}}/$s")"; fi
      side="repo"; [ "${l:-0}" -gt "${r:-0}" ] && side="local"
      echo "$s: differs, $side changed last: $(tr '\n' ' ' <<<"$out")"
    fi
  done
