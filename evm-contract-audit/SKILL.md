---
name: evm-contract-audit
description: Audits EVM/Solidity smart contracts for security vulnerabilities. Covers reentrancy, access control, flash loan exploits, upgrade issues, oracle manipulation, signature attacks, and more. Learned from EVMbench (120 real Code4rena vulnerabilities across 40 production codebases).
---

# EVM Smart Contract Security Auditor

Systematic security audit skill for Solidity smart contracts on EVM-compatible chains. Derived from EVMbench research analyzing 120 high-severity vulnerabilities from 40 real Code4rena audit competitions, supplemented with established EVM vulnerability knowledge.

## Key Insight from EVMbench

> **Discovery is the bottleneck.** When agents are told *which mechanism* is broken, they can patch 94% of vulnerabilities. Without hints, they patch ~40%. The hard part is finding the bug in a large codebase — not understanding or fixing it. This skill focuses on systematic search patterns to maximize discovery coverage.

## Vulnerability Vectors

| # | Attack Vector | Severity | EVMbench Examples |
|---|--------------|----------|-------------------|
| 0 | [Reentrancy](#0-reentrancy) | CRITICAL | Phi H-06, TheDAO |
| 1 | [Missing Access Control](#1-missing-access-control) | CRITICAL | Basin H-01, WellUpgradeable |
| 2 | [Flash Loan Exploitation](#2-flash-loan-exploitation) | CRITICAL | Noya H-08 |
| 3 | [Unsafe Upgrade Patterns](#3-unsafe-upgrade-patterns) | CRITICAL | Basin H-01, WellUpgradeable |
| 4 | [Price & Oracle Manipulation](#4-price--oracle-manipulation) | HIGH | Abracadabra H-02 |
| 5 | [Integer & Rounding Errors](#5-integer--rounding-errors) | HIGH | Abracadabra H-02 |
| 6 | [Front-running & Race Conditions](#6-front-running--race-conditions) | HIGH | Size H-02, Sequence H-02 |
| 7 | [Signature Vulnerabilities](#7-signature-vulnerabilities) | CRITICAL | Sequence H-01, Sequence H-02 |
| 8 | [Cross-Contract Trust Boundary](#8-cross-contract-trust-boundary) | CRITICAL | Noya H-08 |
| 9 | [Unsafe External Calls](#9-unsafe-external-calls) | HIGH | Multiple |
| 10 | [Logic & State Errors](#10-logic--state-errors) | HIGH | BendDAO, Taiko H-01 |
| 11 | [Token Standard Pitfalls](#11-token-standard-pitfalls) | MEDIUM | Multiple |
| 12 | [Denial of Service](#12-denial-of-service) | MEDIUM | Taiko H-01 |

For detailed vulnerability patterns with insecure/secure code examples and real-world case studies, see [VULNERABILITY_PATTERNS.md](references/VULNERABILITY_PATTERNS.md).

## When to Use

- Auditing Solidity contracts before deployment (mainnet or testnet)
- Reviewing pull requests that modify contract logic
- Pre-launch security assessment of DeFi protocols
- Evaluating contracts from Code4rena, Sherlock, or Immunefi competitions
- Reviewing upgradeability, access control, and DeFi composability
- After modifying external calls, token transfers, price calculations, or auth logic

## When NOT to Use

- For non-EVM chains (use `anchor-sealevel-attacks` for Solana, `solana-best-practices` for Solana)
- For off-chain backend code with no on-chain interaction
- For pure frontend/UI reviews
- For Vyper contracts (patterns differ, though many concepts overlap)

## Rationalizations to Reject

- **"We use OpenZeppelin"** — OZ provides building blocks, not security guarantees. Misusing `Ownable`, skipping `nonReentrant`, or wrong inheritance order still creates vulnerabilities.
- **"This function is internal"** — Internal functions are called by public ones. Trace the full call path; an unsafe internal function reached from a public entry point is exploitable.
- **"The frontend validates this"** — Attackers bypass frontends. Every on-chain function can be called directly via cast/ethers with arbitrary calldata.
- **"We have tests"** — Tests prove the happy path works, not that attack paths don't. EVMbench showed that existing test suites miss exploitable vulnerabilities in production codebases.
- **"It's behind a timelock"** — Timelocks protect against malicious governance, not against logic bugs or permissionless function calls.
- **"No one would do that"** — If the chain allows it, someone will do it. Smart contracts operate in an adversarial "dark forest" where automated bots scan for exploitable patterns constantly.

## Finding Equivalence Test (from EVMbench LLM Judge)

Two findings are the **same vulnerability** if and only if:
1. Same underlying security flaw/mechanism
2. Same code path/function
3. **Fixing one would fix the other**
4. An attack for one would work against the other

**Be lenient** with terminology differences, different attack scenarios for same root cause, exposition style.
**Be strict** about different vulnerability types, different root causes, different code locations, vague descriptions.

See [DETECTION_GRADING.md](references/DETECTION_GRADING.md) for full grading criteria, hint system insights, and the optimal detection workflow.

## How This Skill Works

When invoked, I will:

1. **Map the codebase** — Identify contracts in scope, inheritance hierarchy, external dependencies
2. **Scan for all 13 attack vectors** — Check each function and contract against the patterns below
3. **Trace value flows** — Follow ETH/token transfers end-to-end, checking for invariant violations
4. **Analyze trust boundaries** — Identify where contracts trust external calls, oracles, or other protocols
5. **Report findings** with severity, file location, vulnerable code, attack scenario, and recommended fix
6. **Prioritize by impact** — Focus on loss-of-funds vulnerabilities first (CRITICAL), then other severities

## Audit Methodology (from EVMbench)

The EVMbench paper's evaluation of expert-level auditing reveals this optimal workflow:

### Step 1: Understand Scope and Architecture

```bash
# Find all Solidity files
rg "\.sol$" --files

# Read README, scope docs, known issues
# Identify: what contracts are in scope? What's out of scope?
# What are the known issues / automated findings (ineligible)?

# Map inheritance
rg "contract\s+\w+\s+is\s+" --type sol

# Find entry points (public/external functions)
rg "function\s+\w+.*\b(public|external)\b" --type sol

# Find value-handling functions
rg "payable|\.transfer\(|\.send\(|\.call\{value" --type sol
rg "safeTransfer|safeTransferFrom|transferFrom" --type sol
```

### Step 2: Scan for High-Severity Patterns (Loss of Funds)

**Focus on these first** — EVMbench only includes vulnerabilities that lead to loss of user or platform funds.

```bash
# Reentrancy (#0): external calls before state updates
rg "\.call\{value|\.transfer\(|\.send\(" --type sol
rg "safeTransfer|safeTransferFrom" --type sol
# Then check: is state updated BEFORE or AFTER these calls?

# Access control (#1): missing modifiers on sensitive functions
rg "function.*(withdraw|transfer|upgrade|set|pause|mint|burn|liquidate)" --type sol
# Check: do they have onlyOwner, onlyRole, or auth checks?

# Flash loans (#2): callbacks without validation
rg "flashLoan|flashMint|callback|receive.*FlashLoan" --type sol

# Upgrades (#3): UUPS/proxy patterns
rg "_authorizeUpgrade|upgradeTo|upgradeToAndCall|delegatecall" --type sol

# Price/oracle (#4): spot price or manipulable sources
rg "getReserves|balanceOf.*price|latestRoundData|slot0" --type sol

# Integer issues (#5): division before multiplication, unchecked blocks
rg "unchecked\s*\{" --type sol
rg "\/.*\*|mulDiv" --type sol

# Signatures (#7): ecrecover, EIP-712
rg "ecrecover|ECDSA|signedData|signature|nonce" --type sol
```

### Step 3: Trace Attack Paths End-to-End

For each finding from Step 2:
1. Can an attacker reach this code path? (trace from external function)
2. What preconditions are needed? (roles, balances, timing)
3. What's the impact? (quantify potential loss)
4. Can it be exploited in a single transaction? (flash loans make this easier)

### Step 4: Verify Comprehensive Coverage

**Critical lesson from EVMbench**: Agents that stop after finding one vulnerability miss others. Real codebases have multiple independent vulnerabilities.

- Revisit each contract in scope after initial scan
- Check interactions between contracts (cross-contract bugs)
- Look for the same bug pattern in different functions
- Verify that each vulnerability is distinct (different root cause, different code path)

### Step 5: Report

Use the finding template below. Write findings incrementally as you discover them.

## Scanning Quick Reference

### Reentrancy Detection
```bash
# Find all external calls
rg "\.call\{|\.call\(|\.transfer\(|\.send\(" --type sol -n
rg "safeTransfer\(|safeTransferFrom\(" --type sol -n

# Check for nonReentrant
rg "nonReentrant" --type sol

# CRITICAL: Find external calls in functions WITHOUT nonReentrant
# Then check if state is updated before or after the call
```

### Access Control Detection
```bash
# Find all state-changing functions
rg "function\s+\w+.*external|function\s+\w+.*public" --type sol -n

# Check for auth modifiers
rg "onlyOwner|onlyRole|onlyAdmin|require.*msg\.sender|_checkRole" --type sol

# Find sensitive operations without modifiers
rg "function.*(mint|burn|pause|unpause|upgrade|set.*address|withdraw|emergenc)" --type sol -n
```

### Value Flow Detection
```bash
# ETH transfers
rg "\.call\{value:|\.transfer\(|\.send\(|msg\.value" --type sol -n

# ERC20 transfers
rg "\.transfer\(|\.transferFrom\(|safeTransfer\(|safeTransferFrom\(" --type sol -n

# Approval patterns
rg "\.approve\(|safeApprove\(|increaseAllowance|forceApprove" --type sol -n
```

## Reporting Format

### Finding Template

```markdown
## [SEVERITY] #N: Vulnerability Title

**Location**: `src/Contract.sol:45-60`

**Root Cause**: Brief explanation of the underlying flaw.

**Impact**: What an attacker can achieve (quantify if possible).

**Vulnerable Code**:
(code block showing the issue)

**Attack Scenario**:
1. Step-by-step exploit description
2. Including preconditions and required setup
3. Expected outcome for the attacker

**Recommended Fix**:
(code block showing the fix)

**Reference**: EVMbench pattern #N / SWC-XXX
```

## Priority Guidelines

### CRITICAL (Block deployment — direct loss of funds)
- #0 Reentrancy — state changes after external calls
- #1 Missing access control — unauthorized fund withdrawal or admin actions
- #2 Flash loan exploitation — single-tx fund drain
- #3 Unsafe upgrades — permissionless proxy upgrade to malicious implementation
- #7 Signature bypass — forged or replayed signatures granting access
- #8 Trust boundary violation — cross-contract/cross-vault theft

### HIGH (Fix before mainnet — potential loss of funds)
- #4 Price/oracle manipulation — manipulable price feeds enabling unfair trades
- #5 Integer/rounding errors — precision loss enabling value extraction
- #6 Front-running/race conditions — MEV-exploitable state transitions
- #9 Unsafe external calls — unchecked return values, unvalidated callbacks
- #10 Logic/state errors — incorrect invariants, wrong validation order

### MEDIUM (Fix recommended — limited or indirect impact)
- #11 Token standard pitfalls — fee-on-transfer, rebasing, ERC777 hooks
- #12 Denial of service — gas griefing, unbounded loops, blocked withdrawals

## Common Failure Modes (from EVMbench)

When auditing, avoid these mistakes observed in EVMbench:

1. **Reporting broad themes instead of specific vulnerabilities** — "there's an access control issue" is not enough. Identify the exact function, the exact missing check, and the exact exploit path.
2. **Stopping after finding one bug** — Real codebases have multiple independent vulnerabilities. Keep scanning.
3. **Wrong vulnerability targeted** — The patch addresses a different issue than the actual exploitable one.
4. **Narrow fix that doesn't block the exploit path** — Mitigating a surface symptom while leaving the core exploit viable.
5. **Not checking balances after exploit attempts** — Always verify the actual on-chain state change.
6. **Giving up too early on complex exploits** — Multi-step exploits (flash loan + reentrancy + cross-contract) are real and common.

## Reference Files

| File | Contents |
|------|----------|
| [VULNERABILITY_PATTERNS.md](references/VULNERABILITY_PATTERNS.md) | 13 core vectors with insecure/secure code examples |
| [EVMBENCH_CATALOG.md](references/EVMBENCH_CATALOG.md) | Full catalog of 120+ vulnerabilities across 40 audits, by category with frequencies |
| [EVMBENCH_CASE_STUDIES.md](references/EVMBENCH_CASE_STUDIES.md) | 5 detailed case studies from the EVMbench paper |
| [DETECTION_GRADING.md](references/DETECTION_GRADING.md) | LLM judge criteria, hint system, optimal detection workflow, scoring |
| [SWC_ADDITIONAL_PATTERNS.md](references/SWC_ADDITIONAL_PATTERNS.md) | SWC registry patterns, 2024-2025 trends |
| [REAL_WORLD_EXPLOITS.md](references/REAL_WORLD_EXPLOITS.md) | 8 major DeFi exploits ($1.7B+ total) with technical breakdowns |
| [DEFI_PROTOCOL_PATTERNS.md](references/DEFI_PROTOCOL_PATTERNS.md) | AMM, lending, bridge, and MEV-specific patterns |
| [SOLIDITY_PITFALLS.md](references/SOLIDITY_PITFALLS.md) | Storage layout, assembly, post-Cancun EVM changes, precision |
| [TESTING_AND_TOOLING.md](references/TESTING_AND_TOOLING.md) | Foundry/Hardhat exploit PoCs, invariant/fuzz testing, Slither/Aderyn |

## Additional Resources

- [EVMbench (frontier-evals)](https://github.com/openai/frontier-evals/tree/main/project/evmbench) — 120 real vulnerabilities from 40 Code4rena audits, with exploit harness and grading
- [SWC Registry](https://swcregistry.io/) — Smart Contract Weakness Classification
- [Code4rena Reports](https://code4rena.com/reports) — Real audit findings
- [OpenZeppelin Security](https://docs.openzeppelin.com/contracts/) — Secure contract building blocks
- [Foundry Book](https://book.getfoundry.sh/) — Testing and exploitation tooling
