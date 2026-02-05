# Anchor Sealevel Attacks

Comprehensive Solana/Anchor security auditor covering all 11 sealevel attack vectors from [coral-xyz/sealevel-attacks](https://github.com/coral-xyz/sealevel-attacks).

## Overview

This skill systematically scans Solana programs (native Rust and Anchor framework) for every known sealevel attack pattern. Each vulnerability includes insecure, secure, and recommended (idiomatic Anchor) code patterns derived directly from the official sealevel-attacks repository.

## Attack Vectors Covered

| # | Attack | Severity |
|---|--------|----------|
| 0 | Signer Authorization | CRITICAL |
| 1 | Account Data Matching | HIGH |
| 2 | Owner Checks | HIGH |
| 3 | Type Cosplay | HIGH |
| 4 | Initialization / Re-initialization | CRITICAL |
| 5 | Arbitrary CPI | CRITICAL |
| 6 | Duplicate Mutable Accounts | HIGH |
| 7 | Bump Seed Canonicalization | CRITICAL |
| 8 | PDA Sharing | HIGH |
| 9 | Closing Accounts | CRITICAL |
| 10 | Sysvar Address Checking | HIGH |

## Usage

Invoke the skill when auditing any Solana/Anchor program. It will scan for all 11 vulnerability classes and report findings with severity, location, and recommended fixes.

## References

- [Sealevel Attacks Repository](https://github.com/coral-xyz/sealevel-attacks)
- [Anchor Security Exploits](https://www.anchor-lang.com/docs/references/security-exploits)
