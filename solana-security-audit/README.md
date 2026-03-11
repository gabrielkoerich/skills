# Solana Security Audit

Comprehensive Solana smart contract security auditor covering 35 attack vectors across Anchor, native Rust, and Pinocchio frameworks.

## Overview

This skill systematically scans Solana programs for security vulnerabilities across 5 categories: core sealevel attacks, extended security patterns, advanced patterns, native Rust pitfalls, and Pinocchio-specific concerns. Each vulnerability includes insecure and secure code patterns with detection commands.

## Attack Vectors Covered

| Section | Patterns | Scope |
|---------|----------|-------|
| A: Core Sealevel Attacks | A0-A10 (11) | Signer, owner, type cosplay, init, CPI, bump, PDA, closing, sysvar |
| B: Extended Security | B11-B20 (10) | Stale CPI data, arithmetic, drainage, state machines, slippage, casting |
| C: Advanced Patterns | C21-C27 (7) | Remaining accounts, seed collisions, Ed25519, realloc, dependency chains, rent |
| D: Native Rust | D28-D32 (5) | Borsh safety, invoke/invoke_signed, native closure, validation sequence, unsafe |
| E: Pinocchio | E33-E35 (3) | No discriminators, no validation, allocator/lazy entry pitfalls |

## Sources

- [Sealevel Attacks](https://github.com/coral-xyz/sealevel-attacks) -- Original 11 attack patterns
- [SlowMist Best Practices](https://github.com/slowmist/solana-smart-contract-security-best-practices) -- Comprehensive vulnerability catalog
- [Safe Solana Builder](https://github.com/Frankcastleauditor/safe-solana-builder) -- Framework-agnostic patterns
- [Awesome Solana Security](https://github.com/0xMacro/awesome-solana-security) -- Curated resource list
- [Neodyme Common Pitfalls](https://neodyme.io/blog/solana_common_pitfalls/) -- Native Rust pitfalls
- [Ackee Auditors Bootcamp](https://github.com/Ackee-Blockchain/Solana-Auditors-Bootcamp) -- Audit training
- Real-world exploits: Wormhole ($320M), Mango ($115M), Cashio ($48M), Saber, Solend
