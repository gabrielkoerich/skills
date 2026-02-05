# Solana Best Practices

Comprehensive Solana/Anchor development best practices for writing efficient, secure, and maintainable programs.

## Overview

This skill guides development of Solana programs by enforcing best practices across security, performance, and code quality. It covers 14 practice areas, 31 vulnerability patterns, 9 Token-2022 security checks, and 4 real-world exploit case studies -- all with vulnerable/secure code examples.

Based on [SlowMist's security best practices](https://github.com/slowmist/solana-smart-contract-security-best-practices), [Zealynx security checklist](https://www.zealynx.io/blogs/solana-security-checklist), [Helius security guide](https://www.helius.dev/blog/a-hitchhikers-guide-to-solana-program-security), and [bigjoejs' practical guide](https://github.com/bigjoefilms/Solana-program-development-security-best-practices).

## Practice Areas

| # | Practice | Category |
|---|----------|----------|
| 1 | Enforce Signer Checks | Security |
| 2 | Use Typed Anchor Accounts | Security |
| 3 | Validate Ownership and Constraints | Security |
| 4 | Use PDAs Correctly | Security |
| 5 | Validate All Inputs | Security |
| 6 | Handle Errors Properly | Reliability |
| 7 | Calculate Account Space Correctly | Correctness |
| 8 | Reload Accounts After CPI | Correctness |
| 9 | Code Reusability | Maintainability |
| 10 | Comment and Document | Maintainability |
| 11 | Testing | Quality |
| 12 | Security Audits | Quality |
| 13 | Upgradeability | Operations |
| 14 | Compute Unit Management | Performance |

Plus 31 vulnerability patterns covering arithmetic, account validation, state management, CPI security, frontrunning, Token-2022 extensions, and advanced issues (casting, heap exhaustion, Ed25519 introspection, etc.)

## Case Studies

| Exploit | Impact | Root Cause |
|---------|--------|------------|
| Wormhole Bridge | $320M+ | Missing sysvar validation |
| Mango Markets | $115M | Oracle price manipulation |
| Cashio | $48M | Missing account validation |
| Jet Protocol | -- | PDA without caller validation |

## References

- [SlowMist Solana Security Best Practices](https://github.com/slowmist/solana-smart-contract-security-best-practices)
- [Zealynx Solana Security Checklist](https://www.zealynx.io/blogs/solana-security-checklist)
- [Helius Security Guide](https://www.helius.dev/blog/a-hitchhikers-guide-to-solana-program-security)
- [Solana Program Security Best Practices](https://github.com/bigjoefilms/Solana-program-development-security-best-practices)
- [Anchor Documentation](https://www.anchor-lang.com/docs)
- [Solana Toolkit Best Practices](https://solana.com/docs/toolkit/best-practices)
