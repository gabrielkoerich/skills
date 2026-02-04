#!/usr/bin/env bun
/**
 * GitHub Secrets CLI
 * Command-line interface for managing GitHub secrets
 */

import { Command } from 'commander';
import GitHubSecretsClient from './client.js';
import * as fs from 'fs';
import * as path from 'path';

const program = new Command();

function getToken(): string {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('Error: GITHUB_TOKEN environment variable is required');
    console.error('Set it with: export GITHUB_TOKEN="ghp_your_token_here"');
    process.exit(1);
  }
  return token;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

program
  .name('github-secrets')
  .description('CLI for managing GitHub repository secrets')
  .version('1.0.0');

// List command
program
  .command('list')
  .description('List secrets for a repository, organization, or environment')
  .option('-o, --owner <owner>', 'Repository owner')
  .option('-r, --repo <repo>', 'Repository name')
  .option('-g, --org <org>', 'Organization name')
  .option('-e, --environment <env>', 'Environment name')
  .option('-j, --json', 'Output as JSON')
  .option('-v, --visibility', 'Show repository visibility (org secrets only)')
  .action(async (options) => {
    try {
      const client = new GitHubSecretsClient(getToken());

      // Validate options
      if (!options.org && !(options.owner && options.repo)) {
        console.error('Error: Must specify either --org or both --owner and --repo');
        process.exit(1);
      }

      const secrets = await client.listSecrets({
        owner: options.owner,
        repo: options.repo,
        org: options.org,
        environment: options.environment,
      });

      if (options.json) {
        console.log(JSON.stringify(secrets, null, 2));
        return;
      }

      // Table output
      console.log(`\n🔐 Secrets (${secrets.total_count} total)\n`);
      
      if (secrets.total_count === 0) {
        console.log('No secrets found.');
        return;
      }

      // Print header
      if (options.org && options.visibility) {
        console.log(`${'NAME'.padEnd(30)} ${'VISIBILITY'.padEnd(12)} ${'UPDATED'.padEnd(25)}`);
        console.log('-'.repeat(70));
      } else {
        console.log(`${'NAME'.padEnd(30)} ${'UPDATED'.padEnd(25)}`);
        console.log('-'.repeat(60));
      }

      // Print rows
      for (const secret of secrets.secrets) {
        if (options.org && options.visibility && 'visibility' in secret) {
          console.log(
            `${secret.name.padEnd(30)} ${secret.visibility.padEnd(12)} ${formatDate(secret.updated_at).padEnd(25)}`
          );
        } else {
          console.log(`${secret.name.padEnd(30)} ${formatDate(secret.updated_at).padEnd(25)}`);
        }
      }

      console.log();
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

// Get command
program
  .command('get')
  .description('Get metadata for a single secret')
  .option('-o, --owner <owner>', 'Repository owner')
  .option('-r, --repo <repo>', 'Repository name')
  .option('-g, --org <org>', 'Organization name')
  .option('-e, --environment <env>', 'Environment name')
  .requiredOption('-n, --name <name>', 'Secret name')
  .option('-j, --json', 'Output as JSON')
  .action(async (options) => {
    try {
      const client = new GitHubSecretsClient(getToken());

      let secret;
      if (options.org) {
        secret = await client.getOrgSecret(options.org, options.name);
      } else if (options.owner && options.repo) {
        if (options.environment) {
          secret = await client.getEnvSecret(
            options.owner,
            options.repo,
            options.environment,
            options.name
          );
        } else {
          secret = await client.getRepoSecret(options.owner, options.repo, options.name);
        }
      } else {
        console.error('Error: Must specify either --org or both --owner and --repo');
        process.exit(1);
      }

      if (options.json) {
        console.log(JSON.stringify(secret, null, 2));
        return;
      }

      console.log(`\n🔐 Secret: ${secret.name}\n`);
      console.log(`  Created:  ${formatDate(secret.created_at)}`);
      console.log(`  Updated:  ${formatDate(secret.updated_at)}`);
      if ('visibility' in secret) {
        console.log(`  Visibility: ${secret.visibility}`);
      }
      console.log();
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

// Set command
program
  .command('set')
  .description('Create or update a secret')
  .option('-o, --owner <owner>', 'Repository owner')
  .option('-r, --repo <repo>', 'Repository name')
  .option('-g, --org <org>', 'Organization name')
  .option('-e, --environment <env>', 'Environment name')
  .requiredOption('-n, --name <name>', 'Secret name')
  .requiredOption('-v, --value <value>', 'Secret value')
  .option('--repos <repos>', 'Comma-separated list of repos (for org secrets with selected visibility)')
  .action(async (options) => {
    try {
      const client = new GitHubSecretsClient(getToken());

      const repos = options.repos?.split(',').map((r: string) => r.trim()) ?? [];

      await client.setSecret({
        owner: options.owner,
        repo: options.repo,
        org: options.org,
        environment: options.environment,
        name: options.name,
        value: options.value,
        repos: repos.length > 0 ? repos : undefined,
      });

      const location = options.org
        ? `organization ${options.org}`
        : options.environment
        ? `${options.owner}/${options.repo} environment "${options.environment}"`
        : `${options.owner}/${options.repo}`;

      console.log(`✅ Secret "${options.name}" set successfully in ${location}`);
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

// Delete command
program
  .command('delete')
  .description('Delete one or more secrets')
  .option('-o, --owner <owner>', 'Repository owner')
  .option('-r, --repo <repo>', 'Repository name')
  .option('-g, --org <org>', 'Organization name')
  .option('-e, --environment <env>', 'Environment name')
  .requiredOption('-n, --name <name>', 'Secret name(s), comma-separated for multiple')
  .option('-f, --force', 'Skip confirmation prompt')
  .action(async (options) => {
    try {
      const client = new GitHubSecretsClient(getToken());

      const names = options.name.split(',').map((n: string) => n.trim());

      if (!options.force && names.length > 1) {
        console.log(`\n⚠️  You are about to delete ${names.length} secrets:`);
        for (const name of names) {
          console.log(`   - ${name}`);
        }
        console.log();
        
        // Simple confirmation for Bun
        process.stdout.write('Are you sure? (yes/no): ');
        const input = await new Promise<string>((resolve) => {
          process.stdin.once('data', (data) => {
            resolve(data.toString().trim().toLowerCase());
          });
        });
        
        if (input !== 'yes' && input !== 'y') {
          console.log('Cancelled.');
          return;
        }
      }

      const location = options.org
        ? `organization ${options.org}`
        : options.environment
        ? `${options.owner}/${options.repo} environment "${options.environment}"`
        : `${options.owner}/${options.repo}`;

      for (const name of names) {
        await client.deleteSecret(name, {
          owner: options.owner,
          repo: options.repo,
          org: options.org,
          environment: options.environment,
        });
        console.log(`🗑️  Deleted "${name}" from ${location}`);
      }

      console.log(`\n✅ Deleted ${names.length} secret(s) successfully`);
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

// Sync command
program
  .command('sync')
  .description('Sync secrets from a JSON file or .env file')
  .option('-o, --owner <owner>', 'Repository owner')
  .option('-r, --repo <repo>', 'Repository name')
  .option('-g, --org <org>', 'Organization name')
  .option('-e, --environment <env>', 'Environment name')
  .option('-f, --file <file>', 'JSON file with secrets')
  .option('--env-file <file>', '.env file with secrets')
  .option('-d, --dry-run', 'Preview changes without applying')
  .option('--delete-missing', 'Delete secrets not in the file')
  .action(async (options) => {
    try {
      if (!options.file && !options.envFile) {
        console.error('Error: Must specify either --file or --env-file');
        process.exit(1);
      }

      const client = new GitHubSecretsClient(getToken());

      // Parse secrets from file
      let secrets: Record<string, string> = {};
      
      if (options.file) {
        const content = fs.readFileSync(options.file, 'utf-8');
        secrets = JSON.parse(content);
      } else if (options.envFile) {
        const content = fs.readFileSync(options.envFile, 'utf-8');
        for (const line of content.split('\n')) {
          const match = line.match(/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
          if (match) {
            const [, key, value] = match;
            // Remove quotes if present
            secrets[key] = value.replace(/^["'](.*)["']$/, '$1');
          }
        }
      }

      const secretNames = Object.keys(secrets);
      
      if (secretNames.length === 0) {
        console.log('No secrets found in file.');
        return;
      }

      const location = options.org
        ? `organization ${options.org}`
        : options.environment
        ? `${options.owner}/${options.repo} environment "${options.environment}"`
        : `${options.owner}/${options.repo}`;

      console.log(`\n📋 Syncing ${secretNames.length} secrets to ${location}\n`);

      // Get existing secrets
      const existing = await client.listSecrets({
        owner: options.owner,
        repo: options.repo,
        org: options.org,
        environment: options.environment,
      });

      const existingNames = new Set(existing.secrets.map((s) => s.name));

      // Preview changes
      const toAdd: string[] = [];
      const toUpdate: string[] = [];

      for (const name of secretNames) {
        if (existingNames.has(name)) {
          toUpdate.push(name);
        } else {
          toAdd.push(name);
        }
      }

      console.log(`Plan:`);
      console.log(`  🟢 Add:    ${toAdd.length} secrets`);
      console.log(`  🟡 Update: ${toUpdate.length} secrets`);
      
      if (options.deleteMissing) {
        const toDelete = existing.secrets
          .filter((s) => !secretNames.includes(s.name))
          .map((s) => s.name);
        console.log(`  🔴 Delete: ${toDelete.length} secrets`);
      }
      
      console.log();

      if (options.dryRun) {
        console.log('Dry run - no changes made.');
        return;
      }

      // Apply changes
      for (const [name, value] of Object.entries(secrets)) {
        const action = existingNames.has(name) ? 'Updated' : 'Added';
        await client.setSecret({
          owner: options.owner,
          repo: options.repo,
          org: options.org,
          environment: options.environment,
          name,
          value,
        });
        console.log(`  ✅ ${action}: ${name}`);
      }

      // Delete missing if requested
      if (options.deleteMissing) {
        for (const existingSecret of existing.secrets) {
          if (!secrets[existingSecret.name]) {
            await client.deleteSecret(existingSecret.name, {
              owner: options.owner,
              repo: options.repo,
              org: options.org,
              environment: options.environment,
            });
            console.log(`  🗑️  Deleted: ${existingSecret.name}`);
          }
        }
      }

      console.log(`\n✅ Sync complete!`);
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

// Parse and run
program.parse();
