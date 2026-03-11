---
name: solana-best-practices
description: "Reviews Solana/Anchor programs for development best practices. Use when writing, reviewing, improving or auditing Solana smart contracts. 31 vulnerability patterns with 4 real-world case studies."
---

# Solana Smart Contract Best Practices (Audits)

## Common Security Issues
 - Signer enforcement
 - Typed accounts
 - Ownership validation
 - PDA patterns
 - Checked arithmetic
 - Input validation
 - Error handling
 - Account space
 - CPI account reloading
 - Compute units
 - Upgradeability
 - Testing
 - Token-2022 extension security

## Index

### Reference Files
- [DEVELOPMENT_PATTERNS.md](references/DEVELOPMENT_PATTERNS.md) -- 14 practices with full vulnerable/secure code examples
- [COMMON_MISTAKES.md](references/COMMON_MISTAKES.md) -- 31 vulnerability patterns + 4 case studies
- [TOKEN_2022_SECURITY.md](references/TOKEN_2022_SECURITY.md) -- Token-2022 extension security (9 patterns)
- [SECURITY_TESTING.md](references/SECURITY_TESTING.md) -- TDD-style exploit tests for each vulnerability class

### 14 Practice Areas
| # | Practice | Category |
|---|----------|----------|
| 1 | [Signer Checks](#quick-reference-14-practice-areas) | Security |
| 2 | [Typed Accounts](#quick-reference-14-practice-areas) | Security |
| 3 | [Ownership & Constraints](#quick-reference-14-practice-areas) | Security |
| 4 | [PDA Usage](#quick-reference-14-practice-areas) | Security |
| 5 | [Input Validation](#quick-reference-14-practice-areas) | Security |
| 6 | [Error Handling](#quick-reference-14-practice-areas) | Reliability |
| 7 | [Account Space](#quick-reference-14-practice-areas) | Correctness |
| 8 | [Account Reloading](#quick-reference-14-practice-areas) | Correctness |
| 9 | [Code Reusability](#quick-reference-14-practice-areas) | Maintainability |
| 10 | [Documentation](#quick-reference-14-practice-areas) | Maintainability |
| 11 | [Testing](#quick-reference-14-practice-areas) | Quality |
| 12 | [Security Audits](#quick-reference-14-practice-areas) | Quality |
| 13 | [Upgradeability](#quick-reference-14-practice-areas) | Operations |
| 14 | [Compute Units](#quick-reference-14-practice-areas) | Performance |

### 31 Vulnerability Patterns
| # | Vulnerability | Severity |
|---|--------------|----------|
| 1-4 | Arithmetic (overflow, precision, saturating, division by zero) | High |
| 5 | Unhandled errors | High |
| 6-12 | Account validation (permission, signer, writable, owner, init, PDA, system) | High-Critical |
| 13-15 | State management (lamports, oracle, ownership reset) | Low-High |
| 16 | Account reloading after CPI | High |
| 17 | Casting vulnerabilities (`as` casts) | High |
| 18 | Authority transfer pitfalls | High |
| 19 | Account data reallocation | Medium |
| 20 | CPI signer pitfalls | Critical |
| 21 | Security dependency chain | High |
| 22 | Frontrunning / slippage | High |
| 23 | Remaining accounts validation | Medium |
| 24 | Unsafe Rust | High |
| 25 | Vector length bug | Medium |
| 26 | Seed collisions | High |
| 27 | Dangling pointers | High |
| 28 | Account reassignment bug | Medium |
| 29 | Heap exhaustion (32KB limit) | Medium |
| 30 | Account constraint fragility | Medium |
| 31 | Ed25519 introspection | High |

### Token-2022 Security (9 patterns)
| Pattern | Severity |
|---------|----------|
| Token-agnostic interface | High |
| Pre-created ATAs | Medium |
| SPL token validation | High |
| CPIGuard extension | High |
| Default account state | Medium |
| Mint close authority | High |
| Permanent delegate | Critical |
| Transfer hook | High |
| Transfer fees | High |

### Case Studies
| Exploit | Impact | Root Cause |
|---------|--------|------------|
| Wormhole Bridge | $320M+ | Missing sysvar validation |
| Jet Protocol | -- | PDA without caller validation |
| Mango Markets | $115M | Oracle price manipulation |
| Cashio | $48M | Missing account validation |

---

## When to Use

- Writing new Solana/Anchor programs from scratch
- Reviewing pull requests that add or modify program logic
- Refactoring existing programs for security and maintainability
- Preparing a program for mainnet deployment
- Integrating Token-2022 tokens or extensions
- Onboarding developers to Solana best practices
- Post-audit remediation work

## When NOT to Use

- For vulnerability scanning of deployed programs (use `solana-security-audit` instead)
- For non-Solana blockchain code
- For off-chain client/frontend code only
- When the codebase is a Solana SDK library, not a program

## Rationalizations to Reject

- "Rust prevents overflow by default" -- Only in debug mode. Release builds wrap silently. Always use `checked_*()` arithmetic or set `overflow-checks = true` in Cargo.toml.
- "Anchor handles everything" -- Only when you use the correct types. `AccountInfo<'info>` bypasses all checks. `unwrap()` panics your program.
- "We'll add validation later" -- Validation is not a feature; it's structural. Missing it at write-time means missing it at audit-time.
- "The space calculation is close enough" -- Off-by-one in account space causes silent data truncation or allocation failure. Calculate exactly.
- "We don't need tests for constraints" -- Constraints are your security boundary. Every `has_one`, `constraint`, and `seeds` must have a negative test.
- "The account data is fresh, we just wrote it" -- After CPI, Anchor's deserialized account structs are stale. Always call `.reload()`.
- "Token-2022 is just like SPL Token" -- Token-2022 extensions (transfer fees, permanent delegates, CPI guards) change fundamental assumptions. Check every extension.
- "We only accept known tokens" -- Governance changes or new pools can introduce Token-2022 tokens. Code defensively.

## How This Skill Works

When invoked, follow a two-phase approach: **Discover**, then **Fix**.

### Phase 1: Discover (TDD Red)

1. **Scan for Solana programs** in the codebase
2. **Check each practice area** against the 14 development patterns
3. **Scan for vulnerability patterns** across all 31 common mistakes
4. **Check Token-2022 compatibility** if token operations are present
5. **Report findings** grouped by severity (Block Deployment / Fix Before Mainnet / Improve)
6. **For each finding, write an exploit test** that proves the vulnerability exists
   - Use the test patterns from [SECURITY_TESTING.md](references/SECURITY_TESTING.md)
   - The exploit test should PASS when the vulnerability is present (red = vulnerable)
   - This provides evidence and a regression test

### Phase 2: Fix (TDD Green)

7. **Apply the fix** using the secure code patterns from the reference files
8. **Run the exploit test again** -- it should now FAIL (green = fixed)
9. **Write a verification test** that confirms the correct behavior
10. **Run the full test suite** to ensure no regressions

This TDD approach ensures:
- Every vulnerability has **proof** (the exploit test)
- Every fix has **verification** (the exploit test now fails)
- **No regressions** in existing functionality

## Quick Reference: 14 Practice Areas

| # | Practice | Category | Key Check |
|---|----------|----------|-----------|
| 1 | Signer Checks | Security | `Signer<'info>` + `has_one` on all authority ops |
| 2 | Typed Accounts | Security | `Account<'info,T>`, `Program<'info,T>` not `AccountInfo` |
| 3 | Ownership & Constraints | Security | `has_one`, `constraint`, input length validation |
| 4 | PDA Usage | Security | `seeds` + `bump`, stored bump, unique seeds per entity |
| 5 | Input Validation | Security | `checked_*()` arithmetic, range checks, bounds checks |
| 6 | Error Handling | Reliability | `#[error_code]`, `require!`, no `unwrap()`/`panic!` |
| 7 | Account Space | Correctness | Exact calculation: `8 + (4+len) + fields` |
| 8 | Account Reloading | Correctness | `.reload()` after CPI before reading account data |
| 9 | Code Reusability | Maintainability | CPIs, shared crates, modular instruction handlers |
| 10 | Documentation | Maintainability | `///` doc comments, `/// CHECK:` on unchecked accounts |
| 11 | Testing | Quality | Unit + integration + negative tests, `solana-bankrun` |
| 12 | Security Audits | Quality | `cargo-audit`, `clippy`, professional audit before mainnet |
| 13 | Upgradeability | Operations | PDA storage, account versioning, multisig authority |
| 14 | Compute Units | Performance | Profile CU, `ComputeBudgetInstruction`, split heavy txs |

## Review Workflow

### Step 1: Identify Programs

```bash
rg "#\[program\]" programs/
rg "anchor-lang" Cargo.toml
```

### Step 2: Security Checks (Practices 1-5)

```bash
# Raw AccountInfo (Practice 2)
rg "AccountInfo<'info>" programs/

# Missing signer types (Practice 1)
rg "authority.*AccountInfo|admin.*AccountInfo|owner.*AccountInfo" programs/

# Missing constraints (Practice 3)
rg "#\[derive\(Accounts\)\]" programs/ -A 20

# PDA patterns (Practice 4)
rg "seeds\s*=" programs/
rg "bump\s*=" programs/

# Unsafe arithmetic (Practice 5)
rg "\+\s*amount|\-\s*amount|\*\s*amount|/\s*amount" programs/
rg "checked_add|checked_sub|checked_mul|checked_div" programs/

# Unsafe casts (Vulnerability 17)
rg "\bas\s+(u8|u16|u32|u64|i8|i16|i32|i64)" programs/
rg "try_from" programs/
```

### Step 3: Reliability Checks (Practice 6)

```bash
# unwrap/panic in production code
rg "\.unwrap\(\)|panic!\(" programs/

# Custom error types
rg "#\[error_code\]" programs/
rg "require!\(" programs/

# Unsafe blocks (Vulnerability 24)
rg "unsafe\s*\{" programs/
```

### Step 4: Correctness Checks (Practices 7-8)

```bash
# Account space calculations
rg "space\s*=" programs/

# CPI followed by account reads (needs reload)
rg "invoke\(|invoke_signed\(|mint_to\(|transfer\(" programs/ -A 5
rg "\.reload\(\)" programs/

# Remaining accounts (Vulnerability 23)
rg "remaining_accounts" programs/
```

### Step 5: Token-2022 Checks

```bash
# Check if using token operations
rg "token::|token_interface::|TokenInterface|TokenAccount" programs/

# Check for transfer_checked vs transfer
rg "token::transfer\b" programs/  # Should be transfer_checked

# Check for Interface vs Program types
rg "Program<'info,\s*Token>" programs/  # Should be Interface<TokenInterface>

# Token-2022 extension checks
rg "get_extension|StateWithExtensions" programs/
```

### Step 6: Advanced Security Checks

```bash
# Authority transfer patterns (Vulnerability 18)
rg "authority|admin|owner" programs/ -A 3

# Slippage protection (Vulnerability 22)
rg "swap|trade|exchange" programs/
rg "minimum_amount|slippage|deadline" programs/

# Seed collision risk (Vulnerability 26)
rg "seeds\s*=" programs/ | sort

# Heap usage (Vulnerability 29)
rg "Vec::with_capacity|Vec::new|vec!\[" programs/

# Overflow checks in Cargo.toml
rg "overflow-checks" Cargo.toml
```

### Step 7: Quality Checks (Practices 9-14)

```bash
# Documentation
rg "/// CHECK:" programs/
rg "///\s" programs/

# Test coverage
ls tests/
rg "#\[test\]|#\[should_panic\]|it\(" tests/
```

## Reporting Format

```markdown
## [CATEGORY] Practice #N: Practice Name

**Location**: `programs/my-program/src/lib.rs:45`

**Issue**: Description of what's wrong.

**Current Code**:
(vulnerable code block)

**Recommended Fix**:
(secure code block)

**Why**: Explanation of the risk and how the fix prevents it.
```

## Priority Guidelines

### Block Deployment (Critical)
- Missing signer checks on authority operations (#1)
- Raw `AccountInfo` where typed accounts are needed (#2)
- No ownership validation on mutable operations (#3)
- Unchecked arithmetic in financial calculations (#5)
- `unwrap()` or `panic!` in production code (#6)
- CPI signer forwarding to untrusted programs (V20)
- Permanent delegate tokens accepted without checks (Token-2022)
- No slippage protection on swaps (V22)

### Fix Before Mainnet (High)
- Incorrect account space calculations (#7)
- Missing `.reload()` after CPI (#8)
- No PDA seeds or non-deterministic accounts (#4)
- No tests for security constraints (#11)
- No professional audit (#12)
- Unsafe `as` casts on user input (V17)
- Single-step authority transfer (V18)
- Unvalidated remaining accounts (V23)
- Seed collisions between features (V26)
- Transfer fees not accounted for (Token-2022)
- Missing `overflow-checks = true` in Cargo.toml

### Improve for Maintainability (Medium)
- Missing documentation and `/// CHECK:` comments (#10)
- Non-modular instruction handlers (#9)
- No upgrade strategy (#13)
- Unoptimized compute usage (#14)
- No Token-2022 compatibility

## Additional Resources

- [SlowMist Solana Security Best Practices](https://github.com/slowmist/solana-smart-contract-security-best-practices) (original source)
- [Solana Program Security Best Practices](https://github.com/bigjoefilms/Solana-program-development-security-best-practices)
- [Zealynx Solana Security Checklist](https://www.zealynx.io/blogs/solana-security-checklist)
- [Helius Security Guide](https://www.helius.dev/blog/a-hitchhikers-guide-to-solana-program-security)
- [Anchor Documentation](https://www.anchor-lang.com/docs)
- [Solana Toolkit Best Practices](https://solana.com/docs/toolkit/best-practices)
- [Anchor Account Constraints](https://www.anchor-lang.com/docs/references/account-constraints)
