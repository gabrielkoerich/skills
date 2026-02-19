# Additional Vulnerability Patterns (SWC Registry & DeFi Trends)

Patterns that supplement the core 13 vectors from EVMbench. These come from the SWC Registry, DASP Top 10, and real DeFi exploit trends (2024-2025).

---

## Read-Only Reentrancy

**Severity**: HIGH | **SWC**: N/A

An attacker re-enters a **view function** in a *different contract* during a callback. The external contract reads stale intermediate state (e.g., pool reserves mid-withdrawal). First major exploit: Sentiment protocol (April 2023). Widely exploited in Curve/Balancer LP price integrations.

**Detection**:
```bash
rg "get_virtual_price|getRate|getPoolTokenPrice" --type sol -n
# Protocols that read LP token prices from Curve/Balancer during callbacks
```

**Fix**: Use TWAP prices, check upstream pool's reentrancy lock before reading, or add reentrancy-aware wrappers.

---

## First Depositor / ERC-4626 Vault Inflation

**Severity**: HIGH | **SWC**: N/A

In empty ERC-4626 vaults, the first depositor deposits 1 wei (gets 1 share), then donates a large amount directly via `transfer` (not `deposit`). This inflates `totalAssets` while `totalShares = 1`. Subsequent depositors get 0 shares (rounded down).

**Detection**:
```bash
rg "convertToShares|convertToAssets|ERC4626" --type sol -n
# Check if virtual offset is used
rg "_decimalsOffset|deadShares|INITIAL_DEPOSIT" --type sol -n
```

**Fix**: Use OpenZeppelin 4.9+ virtual shares offset (`_decimalsOffset()`), or mint dead shares to `address(1)` on first deposit.

---

## Delegatecall to Untrusted Callee

**Severity**: CRITICAL | **SWC-112**

`delegatecall` executes callee's code in the caller's storage context. If the target is attacker-controlled, they overwrite arbitrary storage (including owner), drain funds, or corrupt state.

**Detection**:
```bash
rg "delegatecall" --type sol -n
# Check if target address is user-supplied or derived from user input
```

**Fix**: Never `delegatecall` to user-controlled addresses. Use whitelists for proxy implementations.

---

## tx.origin Authentication

**Severity**: HIGH | **SWC-115**

`tx.origin` returns the original EOA, not the immediate caller. A malicious contract can trick a user into calling it, then call the vulnerable contract — `tx.origin` passes the check because it's the user's address.

**Detection**:
```bash
rg "tx\.origin" --type sol -n
```

**Fix**: Always use `msg.sender` for authentication. `tx.origin == msg.sender` is only valid for "is this an EOA?" checks (and breaks with account abstraction).

---

## Hash Collision with abi.encodePacked

**Severity**: MEDIUM | **SWC-133**

`abi.encodePacked` with multiple dynamic types omits length prefixes: `abi.encodePacked("ab","c") == abi.encodePacked("a","bc")`. Causes hash collisions in signatures and merkle proofs.

**Detection**:
```bash
rg "abi\.encodePacked" --type sol -n
# Check if two adjacent dynamic types (string, bytes, dynamic array)
```

**Fix**: Use `abi.encode` instead, or never place two dynamic types adjacent in `encodePacked`.

---

## Returnbomb Attack

**Severity**: MEDIUM | **SWC**: N/A

A malicious callee returns an extremely large byte array. Solidity automatically copies return data, and quadratic memory expansion cost consumes all gas. Dangerous in `try/catch` and relayer patterns.

**Detection**:
```bash
rg "\.call\(|try\s+\w+\." --type sol -n
# Check if return data is copied from untrusted external calls
```

**Fix**: Use assembly to limit `returndatacopy` size, or OpenZeppelin's `ExcessivelySafeCall`.

---

## Weak Randomness

**Severity**: HIGH | **SWC-120**

`block.timestamp`, `block.prevrandao`, `blockhash` are predictable or manipulable by validators. `blockhash(block.number)` always returns 0.

**Detection**:
```bash
rg "block\.timestamp.*random|block\.prevrandao|blockhash.*random|keccak256.*block\." --type sol -n
```

**Fix**: Use Chainlink VRF for verifiable randomness. `block.prevrandao` has only 1 bit of entropy per validator.

---

## Uninitialized Proxy / Missing initializer

**Severity**: CRITICAL | **SWC-109**

Implementation contracts without `_disableInitializers()` in the constructor can be directly initialized by attackers. They become owner, then upgrade the proxy to a malicious implementation.

**Detection**:
```bash
rg "Initializable|UUPSUpgradeable" --type sol -n
rg "_disableInitializers" --type sol -n
# Every Initializable contract should have _disableInitializers() in constructor
```

**Fix**: Add `constructor() { _disableInitializers(); }` to all implementation contracts.

---

## Storage Collision in Proxies

**Severity**: HIGH | **SWC**: N/A

New state variables inserted in the middle of a contract between versions collide with existing slots. Changed inheritance order also shifts layout.

**Detection**:
```bash
rg "__gap" --type sol -n
# All upgradeable base contracts should have uint256[N] private __gap
```

**Fix**: Only append new variables at the end. Use `__gap` in base contracts. Use OZ's storage layout checker.

---

## Centralization / Privileged Roles

**Severity**: HIGH | **SWC**: N/A

Powerful admin functions (pause, upgrade, set fees to 100%, sweep funds) create single points of failure. #1 exploit category by dollar value (Ronin $625M, WazirX $230M, Orbit $82M).

**Detection**:
```bash
rg "onlyOwner|onlyAdmin|onlyRole" --type sol -n
# Check what these functions can do: withdraw? upgrade? set fees?
rg "emergencyWithdraw|sweep|migrate|setFee|pause" --type sol -n
```

**Fix**: Use multisig, timelocks (24-48h minimum), upper bounds on adjustable parameters, role separation.

---

## Insufficient Gas Griefing

**Severity**: MEDIUM | **SWC-126**

In relayer/meta-transaction patterns, the relayer forwards with just enough gas for the outer call but not the inner call. Inner call fails silently; relayer still gets paid.

**Detection**:
```bash
rg "gasleft\(\)|gasLimit|relay|forward|meta" --type sol -n
```

**Fix**: Check inner call return values. Validate `gasleft() >= requiredGas` before inner call.

---

## Incorrect EIP-2612 Permit

**Severity**: HIGH | **SWC**: N/A

Custom `permit()` implementations often miss: `ecrecover` returns `address(0)` on invalid sig, `DOMAIN_SEPARATOR` not recomputed on chain forks, nonce not incremented.

**Detection**:
```bash
rg "permit\(|PERMIT_TYPEHASH|DOMAIN_SEPARATOR" --type sol -n
rg "ecrecover" --type sol -n
# Check if using OZ ERC20Permit or custom implementation
```

**Fix**: Use OpenZeppelin's `ERC20Permit`. If custom: recompute domain separator when chainId changes, check signer != address(0), increment nonce.

---

## 2024-2025 DeFi Exploit Trends

1. **Access control / key compromise** — #1 by dollar value (WazirX $230M, Orbit $82M, Radiant $50M)
2. **Read-only reentrancy** — ongoing in Curve/Balancer LP integrations
3. **Cross-chain bridge bugs** — message verification + access control combos
4. **L2-specific issues** — sequencer dependency, `block.number` semantics differ across L2s
5. **ERC-4626 inflation** — legacy vaults without virtual offsets still exploited
6. **Merkle tree attacks** — leaf pre-image, second pre-image in airdrop contracts
7. **Oracle manipulation** — multi-step, multi-protocol, multi-tx attacks replacing simple spot price manipulation

---

## SWC Quick Reference

| SWC | Name | Severity |
|-----|------|----------|
| SWC-100 | Function Default Visibility | MEDIUM |
| SWC-101 | Integer Overflow/Underflow | HIGH |
| SWC-103 | Floating Pragma | LOW |
| SWC-104 | Unchecked Call Return Value | HIGH |
| SWC-105 | Unprotected Ether Withdrawal | CRITICAL |
| SWC-106 | Unprotected SELFDESTRUCT | CRITICAL |
| SWC-107 | Reentrancy | CRITICAL |
| SWC-108 | State Variable Default Visibility | LOW |
| SWC-109 | Uninitialized Storage Pointer | HIGH |
| SWC-110 | Assert Violation | LOW |
| SWC-112 | Delegatecall to Untrusted Callee | CRITICAL |
| SWC-113 | DoS with Failed Call | MEDIUM |
| SWC-114 | Transaction Order Dependence | HIGH |
| SWC-115 | Authorization through tx.origin | HIGH |
| SWC-116 | Block values as Time Proxy | MEDIUM |
| SWC-117 | Signature Malleability | HIGH |
| SWC-118 | Incorrect Constructor Name | CRITICAL |
| SWC-119 | Shadowing State Variables | LOW |
| SWC-120 | Weak Sources of Randomness | HIGH |
| SWC-121 | Missing Protection against Sig Replay | HIGH |
| SWC-122 | Lack of Proper Sig Verification | HIGH |
| SWC-123 | Requirement Violation | MEDIUM |
| SWC-124 | Write to Arbitrary Storage | CRITICAL |
| SWC-126 | Insufficient Gas Griefing | MEDIUM |
| SWC-127 | Arbitrary Jump with Function Type | HIGH |
| SWC-128 | DoS with Block Gas Limit | MEDIUM |
| SWC-129 | Typographical Error | LOW |
| SWC-130 | Right-to-Left Override Control Char | LOW |
| SWC-131 | Presence of Unused Variables | LOW |
| SWC-133 | Hash Collision with abi.encodePacked | MEDIUM |
| SWC-134 | Message Call with Hardcoded Gas | MEDIUM |
| SWC-135 | Code With No Effects | LOW |
| SWC-136 | Unencrypted Private Data On-Chain | HIGH |
