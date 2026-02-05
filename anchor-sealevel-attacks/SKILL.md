
---
name: anchor-sealevel-attacks
description: Audits Solana/Anchor programs for all 11 sealevel attack vectors. Use when auditing Solana smart contracts or reviewing Anchor programs for security.
---

# Anchor Sealevel Attacks Auditor

## Common Attack Vectors

 - Missing signer authorization
 - Account data mismatches
 - Owner check gaps
 - Type cosplay
 - Re-initialization
 - Arbitrary CPI
 - Duplicate mutable accounts
 - Bump seed canonicalization
 - PDA sharing
 - Unsafe account closing
 - Sysvar address spoofing

## When to Use

- Auditing Solana programs (native Rust or Anchor framework) before mainnet deployment
- Reviewing pull requests that modify Solana program logic
- Pre-launch security assessment of Anchor-based protocols
- Validating account constraints, CPI patterns, and PDA usage
- Training or learning about Solana-specific vulnerability patterns
- After modifying instruction handlers, account structs, or CPI logic

## When NOT to Use

- For non-Solana blockchain code (use platform-specific scanners instead)
- For off-chain client code that doesn't contain program logic
- For pure frontend/UI reviews with no on-chain interaction logic
- When the codebase uses a non-Rust Solana SDK (e.g., Seahorse/Python) -- patterns differ

## Rationalizations to Reject

- "Anchor handles this automatically" -- Only if you use the correct types (`Signer<'info>`, `Account<'info, T>`, `Program<'info, T>`). Using raw `AccountInfo<'info>` bypasses all Anchor protections.
- "This account is always passed correctly by our frontend" -- Attackers craft their own transactions. Every account must be validated on-chain.
- "We check the data inside the instruction body" -- Constraints must be in the `#[derive(Accounts)]` struct for Anchor to enforce them before the instruction executes.
- "The PDA can only be derived one way" -- Multiple valid bumps exist for the same seeds. Only the canonical bump (from `find_program_address`) is safe.
- "Nobody would pass the same account twice" -- Duplicate mutable accounts can cause silent data overwrites.
- "We zero the data when closing" -- Without the closed-account discriminator and a force-defund mechanism, lamport top-ups can revive accounts.

## How This Skill Works

When invoked, I will:

1. **Locate Solana programs** -- Find `lib.rs` files under `programs/`, check for `#[program]` or `entrypoint!` markers
2. **Scan for all 11 attack vectors** -- Check each instruction handler and account struct against the patterns below
3. **Report findings** with severity, file location, vulnerable code, and recommended fix
4. **Prioritize by severity** -- CRITICAL findings first, then HIGH, then MEDIUM

## Quick Reference: 11 Attack Vectors

| # | Attack | Severity | What to Check |
|---|--------|----------|---------------|
| 0 | [Signer Authorization](#0-signer-authorization) | CRITICAL | `Signer<'info>` or `is_signer` check |
| 1 | [Account Data Matching](#1-account-data-matching) | HIGH | `constraint` or `has_one` on data fields |
| 2 | [Owner Checks](#2-owner-checks) | HIGH | `Account<'info, T>` or manual `.owner` check |
| 3 | [Type Cosplay](#3-type-cosplay) | HIGH | `Account<'info, T>` with `#[account]` discriminator |
| 4 | [Initialization](#4-initialization) | CRITICAL | `#[account(init)]` or `is_initialized` flag |
| 5 | [Arbitrary CPI](#5-arbitrary-cpi) | CRITICAL | `Program<'info, T>` or program ID validation |
| 6 | [Duplicate Mutable Accounts](#6-duplicate-mutable-accounts) | HIGH | `constraint = a.key() != b.key()` |
| 7 | [Bump Seed Canonicalization](#7-bump-seed-canonicalization) | CRITICAL | `seeds` + `bump` constraint, not user-provided bump |
| 8 | [PDA Sharing](#8-pda-sharing) | HIGH | Unique seeds per user/entity, `seeds` constraint |
| 9 | [Closing Accounts](#9-closing-accounts) | CRITICAL | `#[account(close = dest)]` or discriminator + force-defund |
| 10 | [Sysvar Address Checking](#10-sysvar-address-checking) | HIGH | `Sysvar<'info, T>` or address validation |

For detailed vulnerability patterns with full insecure/secure/recommended code examples, see [VULNERABILITY_PATTERNS.md](references/VULNERABILITY_PATTERNS.md).

## Scanning Workflow

### Step 1: Identify Programs and Framework

```bash
# Find all Solana programs
rg "#\[program\]" programs/          # Anchor programs
rg "entrypoint!" programs/           # Native programs

# Check framework version
rg "anchor-lang" Cargo.toml
rg "solana-program" Cargo.toml
```

Determine if using Anchor or native Rust. Anchor provides built-in protections when correct types are used; native programs need manual checks for everything.

### Step 2: Scan Account Structs (Most Vulnerabilities Live Here)

```bash
# Find all account structs
rg "#\[derive\(Accounts\)\]" programs/ -A 20

# CRITICAL: Find raw AccountInfo usage (bypasses Anchor protections)
rg "AccountInfo<'info>" programs/

# Check for missing Signer type (#0)
rg "authority.*AccountInfo|admin.*AccountInfo|owner.*AccountInfo" programs/

# Check for missing Account type (#2, #3)
rg "AccountInfo<'info>" programs/ # Each one needs justification

# Check for constraints (#1, #6, #8)
rg "#\[account\(" programs/ -A 3
```

**Every `AccountInfo<'info>` in an Anchor program is a red flag.** It should be `Signer<'info>`, `Account<'info, T>`, `Program<'info, T>`, or `Sysvar<'info, T>` unless there is a documented reason with `/// CHECK:` comment.

### Step 3: Scan Instruction Bodies

```bash
# CPI calls (#5)
rg "invoke\(|invoke_signed\(" programs/

# PDA creation (#7, #8)
rg "create_program_address|find_program_address" programs/
rg "seeds.*bump" programs/

# Account closing (#9)
rg "lamports.*borrow_mut|close\s*=" programs/

# Sysvar usage (#10)
rg "load_instruction_at|load_current_index" programs/
```

### Step 4: Cross-Reference Findings

For each finding, verify:
- Is there a corresponding constraint in the `#[derive(Accounts)]` struct?
- Does the instruction body duplicate checks that should be in constraints?
- Are there integration tests that attempt to exploit the vulnerability?

### Step 5: Report

Use the finding template from the reporting section below. Group by severity.

## Reporting Format

### Finding Template

```markdown
## [SEVERITY] Attack #N: Attack Name

**Location**: `programs/my-program/src/lib.rs:45-60`

**Description**: Brief explanation of the vulnerability.

**Vulnerable Code**:
(code block showing the issue)

**Attack Scenario**:
1. Step-by-step exploit description

**Recommended Fix**:
(code block showing idiomatic Anchor fix)

**Reference**: sealevel-attacks #N
```

## Priority Guidelines

### CRITICAL (Block deployment)
- #0 Missing signer authorization -- unauthorized access to any instruction
- #4 Re-initialization -- attacker can overwrite account data
- #5 Arbitrary CPI -- attacker-controlled program execution
- #7 Non-canonical bump seeds -- PDA spoofing, multiple valid addresses
- #9 Unsafe account closing -- account revival attacks

### HIGH (Fix before mainnet)
- #1 Account data mismatch -- operations on wrong accounts
- #2 Missing owner check -- fake account data injection
- #3 Type cosplay -- wrong account type accepted
- #6 Duplicate mutable accounts -- silent data corruption
- #8 PDA sharing -- cross-user fund access
- #10 Sysvar address spoofing -- fake sysvar data

## Testing Recommendations

For each vulnerability class, write negative tests that attempt the exploit:

```typescript
import * as anchor from "@coral-xyz/anchor";

describe("sealevel attack tests", () => {
  // #0: Pass non-signer as authority
  it("rejects unsigned authority", async () => {
    // Craft tx without authority signature
  });

  // #1: Pass mismatched token account
  it("rejects token not owned by signer", async () => {
    // Pass someone else's token account
  });

  // #3: Pass wrong account type
  it("rejects metadata account as user account", async () => {
    // Create Metadata, pass where User expected
  });

  // #5: Pass fake token program
  it("rejects non-SPL token program", async () => {
    // Deploy fake program, pass as token_program
  });

  // #6: Pass same account for both user_a and user_b
  it("rejects duplicate mutable accounts", async () => {
    // Same pubkey for both accounts
  });

  // #9: Revive closed account
  it("prevents closed account revival", async () => {
    // Close account, top up lamports, try to use
  });
});
```

## Additional Resources

- [Sealevel Attacks Repository](https://github.com/coral-xyz/sealevel-attacks) -- All 11 attack examples
- [Anchor Security Exploits](https://www.anchor-lang.com/docs/references/security-exploits) -- Official Anchor documentation
- [Anchor Account Constraints](https://www.anchor-lang.com/docs/references/account-constraints) -- Full constraint reference
- [Solana Security Best Practices](https://docs.solanalabs.com/security) -- Solana Labs security guide
