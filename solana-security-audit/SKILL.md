---
name: solana-security-audit
description: "Comprehensive Solana smart contract security auditor. Covers 25+ attack vectors across Anchor, native Rust, and Pinocchio: sealevel attacks, arithmetic safety, CPI exploits, state machine issues, Token-2022 risks, and real-world case studies."
---

# Solana Security Audit

## Attack Vector Index

### Section A: Core Sealevel Attacks (0-10)
 - A0: Missing signer authorization
 - A1: Account data mismatches
 - A2: Owner check gaps
 - A3: Type cosplay
 - A4: Re-initialization
 - A5: Arbitrary CPI
 - A6: Duplicate mutable accounts
 - A7: Bump seed canonicalization
 - A8: PDA sharing
 - A9: Unsafe account closing
 - A10: Sysvar address spoofing

### Section B: Extended Security Patterns (11-20)
 - B11: Stale account data after CPI
 - B12: Arithmetic safety (overflow, precision, saturating, division by zero, multiply-before-divide)
 - B13: SOL balance drainage via CPI
 - B14: Post-CPI ownership verification
 - B15: State machine inconsistencies
 - B16: Transaction atomicity violations
 - B17: Casting vulnerabilities (`as` truncation)
 - B18: Authority transfer pitfalls (single-step)
 - B19: CPI signer forwarding
 - B20: Frontrunning / missing slippage protection

### Section C: Advanced Patterns (21-27)
 - C21: Remaining accounts validation
 - C22: Seed collisions
 - C23: Ed25519 introspection bypass
 - C24: Account data reallocation stale data
 - C25: Security dependency chain (unconstrained root)
 - C26: Rent-exemption threshold violations
 - C27: Non-atomic initialization race condition

### Section D: Native Rust Patterns (28-32)
 - D28: Borsh deserialization without length pre-checks
 - D29: Native invoke vs invoke_signed misuse
 - D30: Native 3-step safe account closure
 - D31: Missing validation sequence (key → owner → signer → writable → discriminator → data)
 - D32: Unsafe Rust in on-chain programs

### Section E: Pinocchio Framework Patterns (33-35)
 - E33: No automatic discriminators (manual dispatch required)
 - E34: No built-in account validation (all checks manual)
 - E35: `no_allocator!` / `lazy_program_entrypoint!` pitfalls

For detailed patterns with full insecure/secure/recommended code, see [VULNERABILITY_PATTERNS.md](references/VULNERABILITY_PATTERNS.md).

## When to Use

- Auditing Solana programs (Anchor, native Rust, or Pinocchio) before mainnet deployment
- Reviewing pull requests that modify Solana program logic
- Pre-launch security assessment of any Solana-based protocol
- Validating account constraints, CPI patterns, and PDA usage
- Bug bounty recon on deployed programs
- Training or learning about Solana-specific vulnerability patterns
- After modifying instruction handlers, account structs, or CPI logic

## When NOT to Use

- For non-Solana blockchain code (use `evm-contract-audit` for Solidity)
- For off-chain client code that doesn't contain program logic
- For pure frontend/UI reviews with no on-chain interaction logic
- For development best practices, testing, or Token-2022 compatibility guidance (use `solana-best-practices`)

## Rationalizations to Reject

- "Anchor handles this automatically" -- Only if you use the correct types (`Signer<'info>`, `Account<'info, T>`, `Program<'info, T>`). Using raw `AccountInfo<'info>` bypasses all Anchor protections.
- "This account is always passed correctly by our frontend" -- Attackers craft their own transactions. Every account must be validated on-chain.
- "We check the data inside the instruction body" -- Constraints must be in the `#[derive(Accounts)]` struct for Anchor to enforce them before the instruction executes.
- "The PDA can only be derived one way" -- Multiple valid bumps exist for the same seeds. Only the canonical bump (from `find_program_address`) is safe.
- "Nobody would pass the same account twice" -- Duplicate mutable accounts can cause silent data overwrites.
- "We zero the data when closing" -- Without the closed-account discriminator and a force-defund mechanism, lamport top-ups can revive accounts.
- "Rust prevents overflow by default" -- Only in debug mode. Release builds (BPF) wrap silently. Always use `checked_*()` or set `overflow-checks = true`.
- "The account data is fresh, we just wrote it" -- After CPI, Anchor's deserialized account structs are stale. Always call `.reload()`.
- "We validate the account before CPI" -- After CPI returns, the account may have changed owner, been closed, or had lamports drained. Re-validate.
- "Our state transitions are straightforward" -- Without explicit state machine enforcement, attackers can skip states or replay transitions.
- "High code coverage means we're safe" -- Saber's comprehensive fuzzers missed a rounding bug worth $1M/day. Test economic invariants, not just code paths.

## How This Skill Works

When invoked, I will:

1. **Locate Solana programs** -- Find `lib.rs` files under `programs/`, check for `#[program]`, `entrypoint!`, or Pinocchio markers
2. **Determine framework** -- Anchor (with protections), native Rust (manual checks), or Pinocchio (zero-copy, no protections)
3. **Scan for all attack vectors** -- Check each instruction handler and account struct against 35 patterns across sections A-E
4. **Report findings** with severity, file location, vulnerable code, and recommended fix
5. **Prioritize by severity** -- CRITICAL findings first, then HIGH, then MEDIUM

## Quick Reference Tables

### Section A: Core Sealevel Attacks

| # | Attack | Severity | What to Check |
|---|--------|----------|---------------|
| A0 | Signer Authorization | CRITICAL | `Signer<'info>` or `is_signer` check |
| A1 | Account Data Matching | HIGH | `constraint` or `has_one` on data fields |
| A2 | Owner Checks | HIGH | `Account<'info, T>` or manual `.owner` check |
| A3 | Type Cosplay | HIGH | `Account<'info, T>` with `#[account]` discriminator |
| A4 | Initialization | CRITICAL | `#[account(init)]` or `is_initialized` flag |
| A5 | Arbitrary CPI | CRITICAL | `Program<'info, T>` or program ID validation |
| A6 | Duplicate Mutable Accounts | HIGH | `constraint = a.key() != b.key()` |
| A7 | Bump Seed Canonicalization | CRITICAL | `seeds` + `bump`, not user-provided bump |
| A8 | PDA Sharing | HIGH | Unique seeds per user/entity |
| A9 | Closing Accounts | CRITICAL | `close = dest` or discriminator + force-defund |
| A10 | Sysvar Address Checking | HIGH | `Sysvar<'info, T>` or address validation |

### Section B: Extended Security Patterns

| # | Attack | Severity | What to Check |
|---|--------|----------|---------------|
| B11 | Account Reloading After CPI | HIGH | `.reload()` after any CPI that modifies accounts |
| B12 | Arithmetic Safety | HIGH | `checked_*()`, `try_floor`, multiply-before-divide |
| B13 | SOL Balance Drainage via CPI | CRITICAL | Balance checks before/after CPI |
| B14 | Post-CPI Ownership Verification | HIGH | Re-verify `.owner` after CPI returns |
| B15 | State Machine Inconsistencies | HIGH | Explicit state enum, validated transitions |
| B16 | Transaction Atomicity Violations | HIGH | Multi-instruction exploit paths |
| B17 | Casting Vulnerabilities | HIGH | `try_from()` not `as` for narrowing casts |
| B18 | Authority Transfer Pitfalls | HIGH | Two-step nominate/accept pattern |
| B19 | CPI Signer Forwarding | CRITICAL | Protocol PDAs as CPI authorities, never user wallets |
| B20 | Frontrunning / Slippage | HIGH | `minimum_amount_out` + `deadline` parameters |

### Section C: Advanced Patterns

| # | Attack | Severity | What to Check |
|---|--------|----------|---------------|
| C21 | Remaining Accounts | MEDIUM | Manual owner/discriminator/data validation |
| C22 | Seed Collisions | HIGH | Unique prefixes per account type |
| C23 | Ed25519 Introspection | HIGH | Validate position, pubkey, message, nonce |
| C24 | Reallocation Stale Data | MEDIUM | `zero_init = true` after shrink+grow |
| C25 | Security Dependency Chain | CRITICAL | PDA or hardcoded root anchoring all constraints |
| C26 | Rent-Exemption Violations | MEDIUM | Check lamports stay above rent-exempt threshold |
| C27 | Non-Atomic Init Race | HIGH | Atomic create+init in single tx/CPI |

### Section D: Native Rust Patterns

| # | Attack | Severity | What to Check |
|---|--------|----------|---------------|
| D28 | Borsh Deserialization | HIGH | Length pre-check before `try_from_slice` |
| D29 | invoke vs invoke_signed | CRITICAL | Correct signer seeds, PDA authority |
| D30 | Native Account Closure | CRITICAL | Drain + zero + discriminator + force-defund |
| D31 | Validation Sequence | HIGH | key → owner → signer → writable → disc → data |
| D32 | Unsafe Rust | HIGH | Minimize, validate inputs, `// SAFETY:` docs |

### Section E: Pinocchio Framework

| # | Attack | Severity | What to Check |
|---|--------|----------|---------------|
| E33 | No Auto Discriminators | HIGH | Manual instruction dispatch + type tags |
| E34 | No Built-in Validation | HIGH | All checks manual, same as native |
| E35 | Allocator / Lazy Entry | MEDIUM | `no_allocator!` panics, lazy parsing skips |

## Scanning Workflow

### Step 1: Identify Programs and Framework

```bash
# Find all Solana programs
rg "#\[program\]" programs/          # Anchor programs
rg "entrypoint!" programs/           # Native programs
rg "pinocchio" Cargo.toml            # Pinocchio programs
rg "lazy_program_entrypoint" programs/ # Pinocchio lazy entry

# Check framework version
rg "anchor-lang" Cargo.toml
rg "solana-program" Cargo.toml
rg "pinocchio" Cargo.toml

# Check overflow settings
rg "overflow-checks" Cargo.toml
```

Determine framework: Anchor provides built-in protections when correct types are used; native and Pinocchio need manual checks for everything.

### Step 2: Scan Account Structs (Most Vulnerabilities Live Here)

```bash
# Find all account structs (Anchor)
rg "#\[derive\(Accounts\)\]" programs/ -A 20

# CRITICAL: Find raw AccountInfo usage (bypasses Anchor protections)
rg "AccountInfo<'info>" programs/

# Check for missing Signer type (A0)
rg "authority.*AccountInfo|admin.*AccountInfo|owner.*AccountInfo" programs/

# Check for constraints (A1, A6, A8)
rg "#\[account\(" programs/ -A 3

# Check for unconstrained roots (C25)
rg "Account<'info" programs/ | grep -v "seeds\|has_one\|constraint\|init\|close"
```

**Every `AccountInfo<'info>` in an Anchor program is a red flag.** It should be `Signer<'info>`, `Account<'info, T>`, `Program<'info, T>`, or `Sysvar<'info, T>` unless documented with `/// CHECK:`.

### Step 3: Scan Instruction Bodies

```bash
# CPI calls (A5, B11, B13, B14, B19)
rg "invoke\(|invoke_signed\(" programs/
rg "\.reload\(\)" programs/

# PDA creation (A7, A8, C22)
rg "create_program_address|find_program_address" programs/
rg "seeds.*bump" programs/

# Account closing (A9, D30)
rg "lamports.*borrow_mut|close\s*=" programs/
rg "CLOSED_ACCOUNT_DISCRIMINATOR" programs/

# Sysvar usage (A10)
rg "load_instruction_at|load_current_index" programs/

# Arithmetic (B12, B17)
rg "\+\s*amount|\-\s*amount|\*\s*amount|/\s*amount" programs/
rg "checked_add|checked_sub|checked_mul|checked_div" programs/
rg "\bas\s+(u8|u16|u32|u64|i8|i16|i32|i64)" programs/

# State management (B15)
rg "enum.*State|status.*=|state.*=" programs/

# Slippage (B20)
rg "swap|trade|exchange" programs/
rg "minimum_amount|slippage|deadline" programs/

# Ed25519 (C23)
rg "ed25519_program|Ed25519" programs/

# Remaining accounts (C21)
rg "remaining_accounts" programs/

# Realloc (C24)
rg "realloc" programs/
```

### Step 4: Scan for Native/Pinocchio Patterns

```bash
# Borsh deserialization without length checks (D28)
rg "try_from_slice|BorshDeserialize" programs/

# invoke vs invoke_signed confusion (D29)
rg "invoke\(|invoke_signed\(" programs/

# Manual account creation (D31)
rg "create_account|CreateAccount" programs/
rg "next_account_info" programs/ -A 10

# Unsafe blocks (D32)
rg "unsafe\s*\{" programs/

# Pinocchio patterns (E33-35)
rg "no_allocator!|lazy_program_entrypoint" programs/
```

### Step 5: Cross-Reference Findings

For each finding, verify:
- Is there a corresponding constraint in the `#[derive(Accounts)]` struct?
- Does the instruction body duplicate checks that should be in constraints?
- Are there integration tests that attempt to exploit the vulnerability?
- For native/Pinocchio: is the full validation sequence followed (key → owner → signer → writable → discriminator → data)?
- For CPI: is there a `.reload()` after every CPI that modifies accounts read later?
- For arithmetic: is every operation using `checked_*()` or is `overflow-checks = true` in Cargo.toml?

### Step 6: Report

Use the finding template below. Group by severity.

## Reporting Format

### Finding Template

```markdown
## [SEVERITY] #ID: Attack Name

**Location**: `programs/my-program/src/lib.rs:45-60`

**Description**: Brief explanation of the vulnerability.

**Vulnerable Code**:
(code block showing the issue)

**Attack Scenario**:
1. Step-by-step exploit description

**Recommended Fix**:
(code block showing idiomatic fix for the detected framework)

**Reference**: solana-security-audit #ID
```

## Priority Guidelines

### CRITICAL (Block deployment)
- A0 Missing signer authorization -- unauthorized access to any instruction
- A4 Re-initialization -- attacker can overwrite account data
- A5 Arbitrary CPI -- attacker-controlled program execution
- A7 Non-canonical bump seeds -- PDA spoofing
- A9 Unsafe account closing -- account revival attacks
- B13 SOL balance drainage via CPI -- fund theft
- B19 CPI signer forwarding -- user wallet drained via malicious CPI
- C25 Unconstrained dependency chain root -- all downstream validation bypassed
- D29 invoke vs invoke_signed misuse -- unauthorized PDA signing
- D30 Unsafe native account closure -- account revival

### HIGH (Fix before mainnet)
- A1 Account data mismatch -- operations on wrong accounts
- A2 Missing owner check -- fake account data injection
- A3 Type cosplay -- wrong account type accepted
- A6 Duplicate mutable accounts -- silent data corruption
- A8 PDA sharing -- cross-user fund access
- A10 Sysvar address spoofing -- fake sysvar data
- B11 Stale data after CPI -- reading pre-CPI values
- B12 Arithmetic safety -- overflow, precision loss, division by zero
- B14 Post-CPI ownership change -- account taken over during CPI
- B15 State machine inconsistency -- skipped or replayed transitions
- B16 Atomicity violations -- multi-instruction exploits
- B17 Casting vulnerabilities -- silent truncation via `as`
- B18 Authority transfer -- single-step, irrecoverable
- B20 Missing slippage protection -- sandwich attacks
- C22 Seed collisions -- cross-feature PDA overlap
- C23 Ed25519 introspection -- signature verification bypass
- C27 Non-atomic init race -- rent thief pattern
- D28 Borsh deserialization -- buffer overread
- D31 Missing validation sequence -- native program gaps
- D32 Unsafe Rust -- memory safety bypass

### MEDIUM (Improve before mainnet)
- C21 Remaining accounts -- unvalidated dynamic accounts
- C24 Reallocation stale data -- old data exposure
- C26 Rent-exemption violations -- account garbage collection
- E33-35 Pinocchio framework gaps -- manual everything

## Testing Recommendations

For each vulnerability class, write negative tests that attempt the exploit:

```typescript
import * as anchor from "@coral-xyz/anchor";

describe("security audit tests", () => {
  // A0: Pass non-signer as authority
  it("rejects unsigned authority", async () => {});

  // A1: Pass mismatched token account
  it("rejects token not owned by signer", async () => {});

  // A3: Pass wrong account type
  it("rejects metadata account as user account", async () => {});

  // A5: Pass fake token program
  it("rejects non-SPL token program", async () => {});

  // A6: Pass same account for both user_a and user_b
  it("rejects duplicate mutable accounts", async () => {});

  // A9: Revive closed account
  it("prevents closed account revival", async () => {});

  // B11: Read stale data after CPI
  it("returns correct values after CPI", async () => {});

  // B12: Overflow arithmetic
  it("rejects overflowing deposit", async () => {});

  // B13: SOL drainage via CPI
  it("prevents unauthorized lamport transfer via CPI", async () => {});

  // B15: State machine skip
  it("rejects out-of-order state transition", async () => {});

  // B17: Casting overflow
  it("rejects u64 value that truncates to u32", async () => {});

  // B20: Missing slippage
  it("rejects swap below minimum output", async () => {});

  // C25: Unconstrained root
  it("rejects fake config account in dependency chain", async () => {});
});
```

## Real-World Case Studies

| Exploit | Impact | Root Cause | Pattern |
|---------|--------|------------|---------|
| Wormhole Bridge | $320M+ | Missing sysvar validation | A10 |
| Cashio | $48-52M | Missing account validation | A1, A2 |
| Mango Markets | $115M | Oracle price manipulation | B12, B20 |
| Jet Protocol | -- | PDA without caller validation | A8 |
| Saber Stable Swap | ~$1M/day potential | Rounding direction (round vs floor) | B12 |
| Solend Rent Thief | ~0.008 SOL/iter | Non-atomic account init race condition | C27 |
| Step Finance | $27.3M | Admin key compromise (social engineering) | Operational |

## Tools & Resources

### Audit Tools
- [Trident](https://github.com/Ackee-Blockchain/trident) -- Fuzzing framework for Solana programs
- [Anchor X-ray](https://github.com/trailofbits/anchor-x-ray) -- Account visualization (Trail of Bits)
- [Sec3 IDL Guesser](https://github.com/nickvdp/idl-guesser) -- Reverse-engineer program IDLs
- `cargo-audit` -- Dependency vulnerability scanner
- `cargo clippy` -- Lint for common Rust mistakes

### Learning Resources
- [Sealevel Attacks](https://github.com/coral-xyz/sealevel-attacks) -- Original 11 attack examples
- [SlowMist Best Practices](https://github.com/slowmist/solana-smart-contract-security-best-practices) -- Comprehensive vulnerability catalog
- [Safe Solana Builder](https://github.com/Frankcastleauditor/safe-solana-builder) -- Framework-agnostic patterns
- [Awesome Solana Security](https://github.com/0xMacro/awesome-solana-security) -- Curated resource list
- [Solana Security by Example](https://github.com/ubadineke/solana-security-by-example) -- Interactive examples
- [Neodyme Common Pitfalls](https://neodyme.io/blog/solana_common_pitfalls/) -- Native Rust pitfalls
- [Helius Security Guide](https://www.helius.dev/blog/a-hitchhikers-guide-to-solana-program-security) -- Practical walkthrough
- [Ackee Auditors Bootcamp](https://github.com/Ackee-Blockchain/Solana-Auditors-Bootcamp) -- 7-week audit training

### Related Skills
- [solana-best-practices](../solana-best-practices/SKILL.md) -- Development practices, Token-2022 compatibility, testing methodology (31 patterns + 14 practices)
- [solana-dev](../solana-dev/SKILL.md) -- End-to-end development playbook (UI, SDK, Anchor, Pinocchio, testing, payments)

### Official Documentation
- [Anchor Security Exploits](https://www.anchor-lang.com/docs/references/security-exploits)
- [Anchor Account Constraints](https://www.anchor-lang.com/docs/references/account-constraints)
- [Solana Security Best Practices](https://docs.solanalabs.com/security)
