# Solana Security Audit

Comprehensive Solana smart contract security auditor covering 62 attack vectors across Anchor, native Rust, and Pinocchio frameworks.

## Overview

This skill systematically scans Solana programs for security vulnerabilities across 10 categories: core sealevel attacks, extended security patterns, advanced patterns, native Rust pitfalls, Pinocchio-specific concerns, oracle & price feed security, Token-2022 extension risks, modern Anchor & runtime concerns, economic and accounting invariants, and the on-chain/off-chain trust boundary. Each vulnerability includes insecure and secure code patterns with detection commands.

## Attack Vectors Covered

| Section | Patterns | Scope |
|---------|----------|-------|
| A: Core Sealevel Attacks | A0-A10 (11) | Signer, owner, type cosplay, init, CPI, bump, PDA, closing, sysvar |
| B: Extended Security | B11-B20 (10) | Stale CPI data, arithmetic, drainage, state machines, slippage, casting |
| C: Advanced Patterns | C21-C27 (7) | Remaining accounts, seed collisions, Ed25519, realloc, dependency chains, rent |
| D: Native Rust | D28-D32 (5) | Borsh safety, invoke/invoke_signed, native closure, validation sequence, unsafe |
| E: Pinocchio | E33-E35 (3) | No discriminators, no validation, allocator/lazy entry pitfalls |
| F: Oracle & Price Feeds | F36-F38 (3) | Pyth/Switchboard staleness & confidence, spot-price manipulation, feed substitution |
| G: Token-2022 Extensions | G39-G43 (5) | Program confusion, transfer fees, transfer hooks, permanent delegate, amount semantics |
| H: Modern Anchor & Runtime | H44-H51 (8) | init_if_needed, zero-copy, randomness, durable nonce, upgrade authority, compute DoS, cNFT, ALT |
| I: Economic & Accounting Invariants | I52-I59 (8) | Donation DoS, share-price inflation, paired accounting, loss-blind refresh, JIT deposits, full-balance sweeps, unbounded subsidy |
| J: On-Chain / Off-Chain Trust Boundary | J60-J62 (3) | Forged event identity, unbound accounts vs off-chain assumptions, keeper keys on unvalidated input |

## Sources

- [Sealevel Attacks](https://github.com/coral-xyz/sealevel-attacks) -- Original 11 attack patterns
- [SlowMist Best Practices](https://github.com/slowmist/solana-smart-contract-security-best-practices) -- Comprehensive vulnerability catalog
- [Safe Solana Builder](https://github.com/Frankcastleauditor/safe-solana-builder) -- Framework-agnostic patterns
- [Awesome Solana Security](https://github.com/0xMacro/awesome-solana-security) -- Curated resource list
- [Neodyme Common Pitfalls](https://neodyme.io/blog/solana_common_pitfalls/) -- Native Rust pitfalls
- [Ackee Auditors Bootcamp](https://github.com/Ackee-Blockchain/Solana-Auditors-Bootcamp) -- Audit training
- [Pyth](https://docs.pyth.network/price-feeds/best-practices) & [Switchboard](https://docs.switchboard.xyz/) oracle best practices
- [OpenZeppelin ERC-4626 inflation attack](https://docs.openzeppelin.com/contracts/5.x/erc4626) -- donation-based share-price manipulation (I53)
- [SPL Token-2022 Extensions](https://solana.com/developers/guides/token-extensions/getting-started)
- Real-world exploits: Wormhole ($320M), Mango ($115M), Cashio ($48M), Loopscale ($5.8M, 2025), DeFiTuna ($580K, 2026), Drift ($270M, 2026)
