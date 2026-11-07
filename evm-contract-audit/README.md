# EVM Smart Contract Security Auditor

EVM/Solidity security audit skill that covers 13 vulnerability vectors. It is based on EVMbench, a benchmark of 120 real high-severity vulnerabilities from 40 Code4rena audit competitions on production DeFi protocols.

## Overview

The skill scans Solidity smart contracts for known attack patterns, using real-world vulnerability data. Each vulnerability has detection heuristics, insecure and secure code examples, and references to production exploits.

## Vulnerability Vectors Covered

| # | Attack Vector | Severity |
|---|--------------|----------|
| 0 | Reentrancy (classic, cross-function, cross-contract, read-only) | CRITICAL |
| 1 | Missing Access Control | CRITICAL |
| 2 | Flash Loan Exploitation | CRITICAL |
| 3 | Unsafe Upgrade Patterns (UUPS, proxy, beacon) | CRITICAL |
| 4 | Price & Oracle Manipulation | HIGH |
| 5 | Integer & Rounding Errors | HIGH |
| 6 | Front-running & Race Conditions | HIGH |
| 7 | Signature Vulnerabilities (replay, malleability, bypass) | CRITICAL |
| 8 | Cross-Contract Trust Boundary Violations | CRITICAL |
| 9 | Unsafe External Calls | HIGH |
| 10 | Logic & State Errors | HIGH |
| 11 | Token Standard Pitfalls | MEDIUM |
| 12 | Denial of Service | MEDIUM |

## Real-World Case Studies

From EVMbench's dataset of production vulnerabilities:

1. Phi Protocol H-06: reentrancy through an ETH refund drains all curator ETH
2. Basin H-01: a permissionless UUPS upgrade allows a total asset drain (1-line fix)
3. Noya H-08: cross-vault theft through a flash loan and a trusted sender bypass
4. BendDAO: NFT liquidation without an ownership check (1-tx exploit)
5. Abracadabra H-02: an amplified rounding error breaks the AMM pricing invariant

## Usage

Use it to audit any EVM/Solidity smart contract. The skill scans for all 13 vulnerability vectors with grep-based heuristics and manual code review patterns.

## Key Insight

> Discovery is the main bottleneck. With hints about which mechanism is broken, agents patch 94% of vulnerabilities. Without hints, they patch ~40%. This skill gives systematic search patterns to find more bugs.

## Reference Files

| File | Contents |
|------|----------|
| `SKILL.md` | 13 vectors, audit methodology, scanning workflow, finding equivalence test |
| `references/VULNERABILITY_PATTERNS.md` | Core patterns with insecure/secure code examples |
| `references/EVMBENCH_CATALOG.md` | Full catalog of 120+ vulnerabilities across 40 audits, by category |
| `references/EVMBENCH_CASE_STUDIES.md` | 5 detailed case studies + statistical insights |
| `references/DETECTION_GRADING.md` | LLM judge criteria, hint system, optimal detection workflow |
| `references/SWC_ADDITIONAL_PATTERNS.md` | SWC registry + 2024-2025 DeFi exploit trends |
| `references/REAL_WORLD_EXPLOITS.md` | 8 major DeFi exploits ($1.7B+ total) |
| `references/DEFI_PROTOCOL_PATTERNS.md` | AMM, lending, bridge, MEV patterns |
| `references/SOLIDITY_PITFALLS.md` | Storage, assembly, post-Cancun EVM changes |
| `references/TESTING_AND_TOOLING.md` | Foundry/Hardhat testing & static analysis |

## External References

- [EVMbench (frontier-evals)](https://github.com/openai/frontier-evals/tree/main/project/evmbench): 120+ vulnerabilities, exploit harness, grading
- [Code4rena Reports](https://code4rena.com/reports): Real audit findings
- [SWC Registry](https://swcregistry.io/): Smart Contract Weakness Classification
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts/): Secure building blocks
