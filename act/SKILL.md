---
name: act
description: "Run GitHub Actions workflows locally using act. Test CI pipelines, debug jobs, and validate workflows before pushing."
---

# act Skill

Run GitHub Actions workflows locally with [act](https://github.com/nektos/act). Use this to test CI pipelines without pushing to GitHub.

## Prerequisites

- `act` installed (`brew install act`)
- Docker running

## Apple Silicon

Always pass `--container-architecture linux/amd64` on Apple M-series chips:

```bash
act push --container-architecture linux/amd64
```

## Running workflows

Run all jobs triggered by push:

```bash
act push
```

Run a specific job:

```bash
act push -j lint
```

Run multiple specific jobs:

```bash
act push -j lint -j test
```

Run on pull_request event:

```bash
act pull_request
```

Dry run (validate workflow without running containers):

```bash
act push -n
```

## Platform limitations

### macOS runners

`act` cannot run `macos-latest` jobs natively. Skip them or map to a Linux image:

```bash
act push -P macos-latest=catthehacker/ubuntu:act-latest
```

If macOS-specific behavior is needed, test those jobs on real GitHub Actions.

### GitHub Actions that need event context

Some GitHub Actions (like `gitleaks/gitleaks-action@v2`) require the full GitHub event JSON and will fail locally with errors like `Cannot read properties of undefined (reading 'owner')`.

For CI, use the official action:

```yaml
# .github/workflows/ci.yml — works on GitHub Actions
- uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    args: detect --source . --config .gitleaks.toml --no-banner --redact --exit-code=1
```

For local testing with act, install the CLI manually instead:

```bash
# Install gitleaks in the act container
curl -sSfL https://github.com/gitleaks/gitleaks/releases/download/v8.24.2/gitleaks_8.24.2_linux_x64.tar.gz | tar xz
sudo mv gitleaks /usr/local/bin/
gitleaks detect --source . --config .gitleaks.toml --exit-code=1
```

This applies to any action that depends on `github.event` context — prefer CLI equivalents when testing locally.

### Secrets

Pass secrets via `--secret` or `--secret-file`:

```bash
act push --secret GITHUB_TOKEN="$(gh auth token)"
act push --secret-file .secrets
```

The `.secrets` file format is `KEY=VALUE`, one per line.

## Useful flags

| Flag | Description |
|------|-------------|
| `-j <job>` | Run a specific job |
| `-n` | Dry run (validate only) |
| `-l` | List available workflows and jobs |
| `-g` | Draw workflow graph |
| `-v` | Verbose output |
| `-q` | Quiet mode (suppress step output) |
| `-b` | Bind workdir instead of copy (faster, but mutates local files) |
| `--env KEY=VAL` | Set environment variable |
| `--env-file .env` | Load env vars from file |
| `--matrix key:val` | Run specific matrix configuration only |
| `--container-architecture` | Force container arch (e.g. `linux/amd64`) |
| `-P platform=image` | Custom image per platform |

## Listing workflows

```bash
act -l
```

Output shows event triggers, job IDs, and job names — useful for finding the right `-j` target.

## Workflow graph

```bash
act -g
```

Shows job dependencies as a graph.

## Environment variables and inputs

```bash
act push --env NODE_ENV=test --env CI=true
act workflow_dispatch --input version=1.2.3
```

## Common patterns

### Test a single job quickly

```bash
act push -j lint --container-architecture linux/amd64
```

### Validate workflow syntax without running

```bash
act push -n
```

### Run with bind mount (faster iteration)

```bash
act push -j test -b --container-architecture linux/amd64
```

Note: `-b` mounts the working directory directly into the container instead of copying. Faster, but any file changes inside the container affect your local files.

### Debug a failing step

```bash
act push -j test -v --container-architecture linux/amd64
```

The `-v` flag shows detailed Docker and action output.
