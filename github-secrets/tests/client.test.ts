/**
 * Tests for GitHub Secrets Client
 */

import { describe, it, expect, beforeEach, mock } from 'bun:test';
import GitHubSecretsClient from '../src/client';

describe('GitHubSecretsClient', () => {
  let client: GitHubSecretsClient;
  const mockToken = 'ghp_test_token';

  beforeEach(() => {
    client = new GitHubSecretsClient(mockToken);
    // Reset fetch mock
    global.fetch = mock(() =>
      Promise.resolve(new Response(JSON.stringify({}), { status: 200 }))
    );
  });

  describe('constructor', () => {
    it('should create client with token', () => {
      expect(client).toBeDefined();
    });
  });

  describe('listRepoSecrets', () => {
    it('should fetch repository secrets', async () => {
      const mockResponse = {
        total_count: 2,
        secrets: [
          { name: 'SECRET_1', created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-02T00:00:00Z' },
          { name: 'SECRET_2', created_at: '2024-01-03T00:00:00Z', updated_at: '2024-01-04T00:00:00Z' },
        ],
      };

      global.fetch = mock(() =>
        Promise.resolve(
          new Response(JSON.stringify(mockResponse), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      );

      const result = await client.listRepoSecrets('testowner', 'testrepo');

      expect(result.total_count).toBe(2);
      expect(result.secrets).toHaveLength(2);
      expect(result.secrets[0].name).toBe('SECRET_1');
    });

    it('should include correct headers', async () => {
      global.fetch = mock((url: string, options: RequestInit) => {
        expect(options.headers).toMatchObject({
          'Accept': 'application/vnd.github.v3+json',
          'Authorization': `Bearer ${mockToken}`,
        });
        return Promise.resolve(
          new Response(JSON.stringify({ total_count: 0, secrets: [] }), { status: 200 })
        );
      });

      await client.listRepoSecrets('testowner', 'testrepo');
    });
  });

  describe('listOrgSecrets', () => {
    it('should fetch organization secrets', async () => {
      const mockResponse = {
        total_count: 1,
        secrets: [
          { 
            name: 'ORG_SECRET', 
            created_at: '2024-01-01T00:00:00Z', 
            updated_at: '2024-01-02T00:00:00Z',
            visibility: 'all'
          },
        ],
      };

      global.fetch = mock(() =>
        Promise.resolve(
          new Response(JSON.stringify(mockResponse), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          })
        )
      );

      const result = await client.listOrgSecrets('testorg');

      expect(result.total_count).toBe(1);
      expect(result.secrets[0].visibility).toBe('all');
    });
  });

  describe('error handling', () => {
    it('should throw on 401 unauthorized', async () => {
      global.fetch = mock(() =>
        Promise.resolve(
          new Response(JSON.stringify({ message: 'Bad credentials' }), { status: 401 })
        )
      );

      expect(client.listRepoSecrets('testowner', 'testrepo')).rejects.toThrow('401');
    });

    it('should throw on 404 not found', async () => {
      global.fetch = mock(() =>
        Promise.resolve(
          new Response(JSON.stringify({ message: 'Not Found' }), { status: 404 })
        )
      );

      expect(client.listRepoSecrets('testowner', 'testrepo')).rejects.toThrow('404');
    });
  });
});
