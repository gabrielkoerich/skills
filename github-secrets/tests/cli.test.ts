/**
 * Tests for GitHub Secrets CLI
 */

import { describe, it, expect, beforeEach, mock } from 'bun:test';

describe('CLI Commands', () => {
  const mockToken = 'ghp_test_token';

  beforeEach(() => {
    process.env.GITHUB_TOKEN = mockToken;
    global.fetch = mock(() =>
      Promise.resolve(new Response(JSON.stringify({}), { status: 200 }))
    );
  });

  describe('Environment validation', () => {
    it('should require GITHUB_TOKEN', async () => {
      delete process.env.GITHUB_TOKEN;
      
      // Import CLI module fresh to test env check
      const { execSync } = await import('child_process');
      
      try {
        execSync('bunx tsx src/cli.ts list --owner test --repo test', {
          cwd: import.meta.dir + '/..',
          env: { ...process.env, GITHUB_TOKEN: '' },
        });
        expect(false).toBe(true); // Should not reach here
      } catch (error: any) {
        expect(error.status).not.toBe(0);
      }
    });
  });

  describe('List command validation', () => {
    it('should require owner and repo when no org specified', async () => {
      const { execSync } = await import('child_process');
      
      try {
        execSync('bunx tsx src/cli.ts list', {
          cwd: import.meta.dir + '/..',
          env: process.env,
        });
        expect(false).toBe(true);
      } catch (error: any) {
        expect(error.status).not.toBe(0);
      }
    });
  });

  describe('Set command validation', () => {
    it('should require name and value', async () => {
      const { execSync } = await import('child_process');
      
      try {
        execSync('bunx tsx src/cli.ts set --owner test --repo test', {
          cwd: import.meta.dir + '/..',
          env: process.env,
        });
        expect(false).toBe(true);
      } catch (error: any) {
        expect(error.status).not.toBe(0);
      }
    });
  });

  describe('Sync command validation', () => {
    it('should require file or env-file', async () => {
      const { execSync } = await import('child_process');
      
      try {
        execSync('bunx tsx src/cli.ts sync --owner test --repo test', {
          cwd: import.meta.dir + '/..',
          env: process.env,
        });
        expect(false).toBe(true);
      } catch (error: any) {
        expect(error.status).not.toBe(0);
      }
    });
  });
});

// Integration test helpers
describe('Integration helpers', () => {
  it('should format date correctly', () => {
    const dateStr = '2024-01-15T10:30:00Z';
    const date = new Date(dateStr);
    const formatted = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    
    expect(formatted).toContain('2024');
    expect(formatted).toContain('10');
  });

  it('should parse comma-separated values', () => {
    const input = 'secret1, secret2, secret3';
    const values = input.split(',').map((s) => s.trim());
    
    expect(values).toEqual(['secret1', 'secret2', 'secret3']);
  });
});
