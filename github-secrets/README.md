# GitHub Secrets Manager

A TypeScript/Bun CLI tool for managing GitHub repository, organization, and environment secrets via the GitHub API.

## Features

- 🔐 **List secrets** - View all secrets with metadata
- ➕ **Add secrets** - Create new secrets with automatic encryption
- 📝 **Update secrets** - Modify existing secrets
- 🗑️ **Delete secrets** - Remove single or multiple secrets
- 🔄 **Sync secrets** - Bulk import from JSON or .env files
- 🏢 **Multi-level support** - Repository, organization, and environment secrets

## Why This Tool?

While `gh secret` covers basic operations (list, set, delete), this custom tool adds workflow features that `gh` doesn't provide:

| Feature | `gh secret` | github-secrets |
|---------|-------------|----------------|
| Bulk import from `.env` | One secret per file | Full file sync |
| Dry-run preview | No | `--dry-run` flag |
| Delete missing secrets | No | `--delete-missing` flag |
| Batch delete multiple | One at a time | Comma-separated in one command |
| Org secrets to selected repos | No | `--repos` flag |

**Use `gh` for:** Quick single-secret operations.
**Use github-secrets for:** Bulk sync workflows, exact replication of local `.env` files to GitHub, and safe preview before applying changes.

## Installation

```bash
cd skills/github-secrets
bun install
```

## Configuration

Set your GitHub Personal Access Token:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

**Required scopes:**
- `repo` - For repository secrets
- `admin:org` - For organization secrets

## Quick Start

```bash
# List repository secrets
bun run list --owner myuser --repo myrepo

# Add a secret
bun run set --owner myuser --repo myrepo --name API_KEY --value "secret123"

# Delete a secret
bun run delete --owner myuser --repo myrepo --name API_KEY

# Sync from .env file
bun run sync --owner myuser --repo myrepo --env-file .env
```

## Commands

### `list`
List secrets for a repository, organization, or environment.

```bash
# Repository secrets
bun run list --owner <owner> --repo <repo>

# Organization secrets
bun run list --org <org>

# Environment secrets
bun run list --owner <owner> --repo <repo> --environment <env>

# JSON output
bun run list --owner <owner> --repo <repo> --json
```

### `get`
Get metadata for a single secret.

```bash
bun run get --owner <owner> --repo <repo> --name <secret_name>
```

### `set`
Create or update a secret.

```bash
# Repository secret
bun run set --owner <owner> --repo <repo> --name <name> --value <value>

# Organization secret
bun run set --org <org> --name <name> --value <value>

# Organization secret with selected repositories
bun run set --org <org> --name <name> --value <value> --repos repo1,repo2

# Environment secret
bun run set --owner <owner> --repo <repo> --environment <env> --name <name> --value <value>
```

### `delete`
Delete one or more secrets.

```bash
# Single secret
bun run delete --owner <owner> --repo <repo> --name <name>

# Multiple secrets
bun run delete --owner <owner> --repo <repo> --name "SECRET1,SECRET2,SECRET3"

# Skip confirmation
bun run delete --owner <owner> --repo <repo> --name <name> --force
```

### `sync`
Sync secrets from a file.

```bash
# From JSON file
bun run sync --owner <owner> --repo <repo> --file secrets.json

# From .env file
bun run sync --owner <owner> --repo <repo> --env-file .env

# Dry run (preview changes)
bun run sync --owner <owner> --repo <repo> --file secrets.json --dry-run

# Delete secrets not in file
bun run sync --owner <owner> --repo <repo> --file secrets.json --delete-missing
```

**JSON format:**
```json
{
  "API_KEY": "value1",
  "DATABASE_URL": "value2",
  "SECRET_TOKEN": "value3"
}
```

## Testing

```bash
# Run all tests
bun test

# Run with coverage
bun test --coverage

# Type check
bun run typecheck
```

## Project Structure

```
github-secrets/
├── src/
│   ├── client.ts     # GitHub API client
│   └── cli.ts        # CLI interface
├── tests/
│   ├── client.test.ts
│   └── cli.test.ts
├── SKILL.md          # Skill documentation
├── README.md         # This file
├── package.json
└── tsconfig.json
```

## API Reference

The `GitHubSecretsClient` class provides direct programmatic access:

```typescript
import GitHubSecretsClient from './src/client';

const client = new GitHubSecretsClient(process.env.GITHUB_TOKEN!);

// List secrets
const secrets = await client.listRepoSecrets('owner', 'repo');

// Set secret
await client.setRepoSecret('owner', 'repo', 'SECRET_NAME', 'value');

// Delete secret
await client.deleteRepoSecret('owner', 'repo', 'SECRET_NAME');
```

## Security

- Secrets are encrypted using libsodium sealed boxes before transmission
- Secret values are never logged or stored locally
- Always use environment variables for tokens
- Use `--dry-run` to preview changes before applying

## License

MIT
