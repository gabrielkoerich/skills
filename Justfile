set shell := ["bash", "-euo", "pipefail", "-c"]

# Show available recipes
@default:
  just --list

# Lint all skills (check mode)
lint-skills:
  ./skill-lint/scripts/lint-skills.sh

# Lint all skills and auto-fix safe issues
lint-skills-fix:
  ./skill-lint/scripts/lint-skills.sh --fix

# Scaffold a new skill directory with SKILL.md + agents/openai.yaml
scaffold-skill name description:
  ./skill-creator/scripts/init-skill.sh "{{name}}" "{{description}}"

# Build PR body preview from current branch
pr-body base="main":
  ./gh-pr-polish/scripts/make-pr-body.sh "{{base}}"

# Create PR from current branch
pr-create base="main":
  ./gh-pr-polish/scripts/create-pr.sh "{{base}}"

# Worktree janitor shortcuts
wt-list:
  ./worktree-janitor/scripts/janitor.sh list

wt-audit:
  ./worktree-janitor/scripts/janitor.sh audit

wt-prune:
  ./worktree-janitor/scripts/janitor.sh prune

wt-remove path:
  ./worktree-janitor/scripts/janitor.sh remove "{{path}}"
