/**
 * GitHub Secrets API Client
 * Handles encryption and API communication for managing GitHub secrets
 */

import sodium from 'libsodium-wrappers-sumo';

export interface Secret {
  name: string;
  created_at: string;
  updated_at: string;
}

export interface SecretList {
  total_count: number;
  secrets: Secret[];
}

export interface OrgSecret extends Secret {
  visibility: 'all' | 'private' | 'selected';
  selected_repositories_url?: string;
}

export interface OrgSecretList {
  total_count: number;
  secrets: OrgSecret[];
}

export interface PublicKey {
  key_id: string;
  key: string;
}

export interface SetSecretOptions {
  owner?: string;
  repo?: string;
  org?: string;
  environment?: string;
  name: string;
  value: string;
  repos?: string[]; // For org secrets with selected visibility
}

export interface ListSecretsOptions {
  owner?: string;
  repo?: string;
  org?: string;
  environment?: string;
}

export class GitHubSecretsClient {
  private token: string;
  private baseUrl = 'https://api.github.com';

  constructor(token: string) {
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': `Bearer ${this.token}`,
        'X-GitHub-Api-Version': '2022-11-28',
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`GitHub API error (${response.status}): ${error}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json() as Promise<T>;
  }

  private async getPublicKey(
    ownerOrOrg: string,
    repo?: string,
    environment?: string
  ): Promise<PublicKey> {
    if (repo && environment) {
      // Environment-level secret
      return this.request<PublicKey>(
        `/repos/${ownerOrOrg}/${repo}/environments/${environment}/secrets/public-key`
      );
    } else if (repo) {
      // Repository-level secret
      return this.request<PublicKey>(
        `/repos/${ownerOrOrg}/${repo}/actions/secrets/public-key`
      );
    } else {
      // Organization-level secret
      return this.request<PublicKey>(
        `/orgs/${ownerOrOrg}/actions/secrets/public-key`
      );
    }
  }

  private async encryptSecret(value: string, publicKey: string): Promise<string> {
    await sodium.ready;
    
    // Decode the base64 public key
    const binaryKey = sodium.from_base64(publicKey, sodium.base64_variants.ORIGINAL);
    
    // Encrypt the secret using libsodium sealed box
    const encrypted = sodium.crypto_box_seal(
      sodium.from_string(value),
      binaryKey
    );
    
    // Return base64-encoded encrypted value
    return sodium.to_base64(encrypted, sodium.base64_variants.ORIGINAL);
  }

  // List repository secrets
  async listRepoSecrets(owner: string, repo: string): Promise<SecretList> {
    return this.request<SecretList>(`/repos/${owner}/${repo}/actions/secrets`);
  }

  // List organization secrets
  async listOrgSecrets(org: string): Promise<OrgSecretList> {
    return this.request<OrgSecretList>(`/orgs/${org}/actions/secrets`);
  }

  // List environment secrets
  async listEnvSecrets(
    owner: string,
    repo: string,
    environment: string
  ): Promise<SecretList> {
    return this.request<SecretList>(
      `/repos/${owner}/${repo}/environments/${environment}/secrets`
    );
  }

  // Get single repository secret metadata
  async getRepoSecret(
    owner: string,
    repo: string,
    name: string
  ): Promise<Secret> {
    return this.request<Secret>(
      `/repos/${owner}/${repo}/actions/secrets/${name}`
    );
  }

  // Get single organization secret metadata
  async getOrgSecret(org: string, name: string): Promise<OrgSecret> {
    return this.request<OrgSecret>(`/orgs/${org}/actions/secrets/${name}`);
  }

  // Get single environment secret metadata
  async getEnvSecret(
    owner: string,
    repo: string,
    environment: string,
    name: string
  ): Promise<Secret> {
    return this.request<Secret>(
      `/repos/${owner}/${repo}/environments/${environment}/secrets/${name}`
    );
  }

  // Set repository secret
  async setRepoSecret(
    owner: string,
    repo: string,
    name: string,
    value: string
  ): Promise<void> {
    const { key_id, key } = await this.getPublicKey(owner, repo);
    const encryptedValue = await this.encryptSecret(value, key);

    await this.request(
      `/repos/${owner}/${repo}/actions/secrets/${name}`,
      {
        method: 'PUT',
        body: JSON.stringify({
          encrypted_value: encryptedValue,
          key_id,
        }),
      }
    );
  }

  // Set organization secret
  async setOrgSecret(
    org: string,
    name: string,
    value: string,
    visibility: 'all' | 'private' | 'selected' = 'all',
    repos?: string[]
  ): Promise<void> {
    const { key_id, key } = await this.getPublicKey(org);
    const encryptedValue = await this.encryptSecret(value, key);

    const body: Record<string, unknown> = {
      encrypted_value: encryptedValue,
      key_id,
      visibility,
    };

    if (visibility === 'selected' && repos && repos.length > 0) {
      // Need to get repository IDs first
      const repoIds = await this.getRepoIds(org, repos);
      body.selected_repository_ids = repoIds;
    }

    await this.request(`/orgs/${org}/actions/secrets/${name}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  // Set environment secret
  async setEnvSecret(
    owner: string,
    repo: string,
    environment: string,
    name: string,
    value: string
  ): Promise<void> {
    const { key_id, key } = await this.getPublicKey(owner, repo, environment);
    const encryptedValue = await this.encryptSecret(value, key);

    await this.request(
      `/repos/${owner}/${repo}/environments/${environment}/secrets/${name}`,
      {
        method: 'PUT',
        body: JSON.stringify({
          encrypted_value: encryptedValue,
          key_id,
        }),
      }
    );
  }

  // Delete repository secret
  async deleteRepoSecret(owner: string, repo: string, name: string): Promise<void> {
    await this.request(`/repos/${owner}/${repo}/actions/secrets/${name}`, {
      method: 'DELETE',
    });
  }

  // Delete organization secret
  async deleteOrgSecret(org: string, name: string): Promise<void> {
    await this.request(`/orgs/${org}/actions/secrets/${name}`, {
      method: 'DELETE',
    });
  }

  // Delete environment secret
  async deleteEnvSecret(
    owner: string,
    repo: string,
    environment: string,
    name: string
  ): Promise<void> {
    await this.request(
      `/repos/${owner}/${repo}/environments/${environment}/secrets/${name}`,
      {
        method: 'DELETE',
      }
    );
  }

  // Helper: Get repository IDs from names
  private async getRepoIds(org: string, repoNames: string[]): Promise<number[]> {
    const ids: number[] = [];
    for (const name of repoNames) {
      try {
        const repo = await this.request<{ id: number }>(`/repos/${org}/${name}`);
        ids.push(repo.id);
      } catch (error) {
        console.warn(`Warning: Could not find repository ${org}/${name}`);
      }
    }
    return ids;
  }

  // Generic list method
  async listSecrets(options: ListSecretsOptions): Promise<SecretList | OrgSecretList> {
    if (options.org) {
      return this.listOrgSecrets(options.org);
    } else if (options.owner && options.repo) {
      if (options.environment) {
        return this.listEnvSecrets(options.owner, options.repo, options.environment);
      }
      return this.listRepoSecrets(options.owner, options.repo);
    }
    throw new Error('Must specify either org or owner+repo');
  }

  // Generic set method
  async setSecret(options: SetSecretOptions): Promise<void> {
    if (options.org) {
      const visibility = options.repos && options.repos.length > 0 ? 'selected' : 'all';
      return this.setOrgSecret(
        options.org,
        options.name,
        options.value,
        visibility,
        options.repos
      );
    } else if (options.owner && options.repo) {
      if (options.environment) {
        return this.setEnvSecret(
          options.owner,
          options.repo,
          options.environment,
          options.name,
          options.value
        );
      }
      return this.setRepoSecret(options.owner, options.repo, options.name, options.value);
    }
    throw new Error('Must specify either org or owner+repo');
  }

  // Generic delete method
  async deleteSecret(
    name: string,
    options: ListSecretsOptions
  ): Promise<void> {
    if (options.org) {
      return this.deleteOrgSecret(options.org, name);
    } else if (options.owner && options.repo) {
      if (options.environment) {
        return this.deleteEnvSecret(options.owner, options.repo, options.environment, name);
      }
      return this.deleteRepoSecret(options.owner, options.repo, name);
    }
    throw new Error('Must specify either org or owner+repo');
  }
}

export default GitHubSecretsClient;
