---
name: github-secrets
description: Manage GitHub repository secrets via the GitHub API. Supports listing, adding, updating, and deleting repository and organization secrets. Use when user needs to manage GitHub Actions secrets, environment variables, or repository-level secrets securely.
homepage: https://docs.github.com/en/rest/actions/secrets
---

# GitHub Secrets Manager

Manage GitHub repository and organization secrets securely via the GitHub API.

## Setup

### 1. GitHub Token
Set your GitHub Personal Access Token with `repo` and `admin:org` scopes:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

**Required scopes:**
- `repo` - For repository secrets
- `admin:org` - For organization secrets

### 2. Install Dependencies

```bash
cd skills/github-secrets
bun install
```

## CLI Commands

### List Secrets

**Repository secrets:**
```bash
# List all repository secrets
bun run list --owner myuser --repo myrepo

# List with values (masked)
bun run list --owner myuser --repo myrepo --show-values
```

**Organization secrets:**
```bash
# List organization secrets
bun run list --org myorganization

# List with repository visibility
bun run list --org myorganization --visibility
```

**Environment secrets:**
```bash
# List secrets for a specific environment
bun run list --owner myuser --repo myrepo --environment production
```

### Add/Update Secrets

**Add a new secret:**
```bash
# Add repository secret
bun run set --owner myuser --repo myrepo --name API_KEY --value "secret123"

# Add organization secret (visible to all repos)
bun run set --org myorganization --name API_KEY --value "secret123"

# Add organization secret with selected repositories
bun run set --org myorganization --name API_KEY --value "secret123" --repos repo1,repo2,repo3

# Add environment secret
bun run set --owner myuser --repo myrepo --environment production --name API_KEY --value "secret123"
```

**Update existing secret:**
```bash
# Same command as add - will overwrite existing secret
bun run set --owner myuser --repo myrepo --name API_KEY --value "newvalue456"
```

### Delete Secrets

```bash
# Delete repository secret
bun run delete --owner myuser --repo myrepo --name API_KEY

# Delete organization secret
bun run delete --org myorganization --name API_KEY

# Delete environment secret
bun run delete --owner myuser --repo myrepo --environment production --name API_KEY

# Delete multiple secrets
bun run delete --owner myuser --repo myrepo --name "SECRET1,SECRET2,SECRET3"
```

### Get Single Secret

```bash
# Get secret metadata (created/updated dates)
bun run get --owner myuser --repo myrepo --name API_KEY

# Get with decrypted value (only for Codespaces user secrets)
bun run get --owner myuser --repo myrepo --name API_KEY --decrypt
```

### Sync Secrets

Sync secrets from a JSON file or environment file:

```bash
# Sync from JSON file
bun run sync --owner myuser --repo myrepo --file secrets.json

# Sync from .env file
bun run sync --owner myuser --repo myrepo --env-file .env

# Preview changes (dry run)
bun run sync --owner myuser --repo myrepo --file secrets.json --dry-run
```

**secrets.json format:**
```json
{
  "API_KEY": "value1",
  "DATABASE_URL": "value2",
  "SECRET_TOKEN": "value3"
}
```

## API Reference

### Types

```typescript
interface Secret {
  name: string;
  created_at: string;
  updated_at: string;
}

interface SecretList {
  total_count: number;
  secrets: Secret[];
}

interface SecretValue {
  name: string;
  value: string;
  environment?: string;
}
```

### Methods

| Method | Description |
|--------|-------------|
| `listRepoSecrets(owner, repo)` | List all repository secrets |
| `listOrgSecrets(org)` | List all organization secrets |
| `listEnvSecrets(owner, repo, env)` | List environment secrets |
| `getSecret(owner, repo, name)` | Get secret metadata |
| `setSecret(owner, repo, name, value)` | Create/update secret |
| `deleteSecret(owner, repo, name)` | Delete a secret |
| `syncSecrets(owner, repo, secrets)` | Bulk sync secrets |

## Security Notes

- Secrets are encrypted using libsodium sealed boxes before being sent to GitHub
- Secret values are never logged or stored locally
- Use `--dry-run` flag to preview changes before applying
- Always use environment variables or secure secret stores for token values

## Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid token | Check GITHUB_TOKEN is valid |
| `403 Forbidden` | Insufficient permissions | Ensure token has required scopes |
| `404 Not Found` | Repo/secret doesn't exist | Verify owner/repo/secret name |
| `422 Validation Failed` | Invalid secret name | Use valid secret name format |

## Testing

```bash
# Run all tests
bun test

# Run with coverage
bun test --coverage

# Run specific test file
bun test tests/list.test.ts
```

## Examples

### CI/CD Setup

```bash
# Set deployment secrets
bun run set --owner myuser --repo myapp --name DEPLOY_TOKEN --value "$DEPLOY_TOKEN"
bun run set --owner myuser --repo myapp --name AWS_ACCESS_KEY --value "$AWS_KEY"
bun run set --owner myuser --repo myapp --name AWS_SECRET_KEY --value "$AWS_SECRET"
```

### Migration Between Repos

```bash
# Export from source repo
bun run list --owner oldowner --repo oldrepo --json > secrets.json

# Import to target repo
bun run sync --owner newowner --repo newrepo --file secrets.json
```
