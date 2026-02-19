# Solidity & EVM-Specific Pitfalls

Language-level and EVM-level pitfalls that go beyond high-level vulnerability patterns. Covers storage layout, assembly, post-Cancun changes, and precision issues.

---

## Storage Layout in Proxies

When using proxy patterns (UUPS, Transparent, Beacon), storage lives in the proxy's context. If the implementation's storage layout changes between upgrades, slots collide.

```solidity
// Implementation V1
contract V1 {
    uint256 public value;      // slot 0
    address public owner;      // slot 1
}

// VULNERABLE V2 -- inserted variable shifts slots
contract V2_BAD {
    uint256 public value;      // slot 0 -- OK
    uint256 public newField;   // slot 1 -- COLLISION: overwrites owner!
    address public owner;      // slot 2 -- wrong slot
}

// SECURE V2 -- append only
contract V2_GOOD {
    uint256 public value;      // slot 0
    address public owner;      // slot 1
    uint256 public newField;   // slot 2 -- appended at end
}

// BEST PRACTICE: Use storage gaps
contract V1 {
    uint256 public value;
    address public owner;
    uint256[48] private __gap;  // Reserve 48 slots
}
```

**EIP-7201 (Namespaced Storage):**
```solidity
library StorageLib {
    bytes32 constant MAIN_STORAGE_SLOT = 0x...;  // Deterministic

    struct MainStorage {
        uint256 value;
        address owner;
        mapping(address => uint256) balances;
    }

    function getMainStorage() internal pure returns (MainStorage storage s) {
        bytes32 slot = MAIN_STORAGE_SLOT;
        assembly { s.slot := slot }
    }
}
```

```bash
rg -n "__gap|_gap|__reserved" --type sol
rg -n "delegatecall|_implementation|ERC1967|UUPS|TransparentProxy" --type sol
# Compare layouts: forge inspect ContractV1 storage-layout --pretty
```

---

## Constructor vs Initializer in Upgradeable Contracts

Constructors run only on the implementation's deployment, NOT in the proxy's context.

```solidity
// VULNERABLE: Constructor in upgradeable contract
contract MyTokenV1 is UUPSUpgradeable {
    address public owner;
    constructor() {
        owner = msg.sender;  // Sets in IMPLEMENTATION storage, not proxy
    }
    // When called via proxy, owner is address(0)!
}

// SECURE: Use initializer
contract MyTokenV1 is UUPSUpgradeable, Initializable {
    address public owner;

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() { _disableInitializers(); }

    function initialize(address _owner) external initializer {
        owner = _owner;  // Runs in proxy context
    }
}
```

```bash
rg -n "constructor()" --type sol
rg -n "_disableInitializers" --type sol
rg -n "function initialize|function __.*_init" --type sol
```

---

## Solidity 0.8.x Specific Issues

### Unchecked Blocks Bypass Overflow Protection

```solidity
function danger(uint256 x) external pure returns (uint256) {
    unchecked {
        return x + 1;  // Can overflow silently!
    }
}
```

```bash
rg -n "unchecked" --type sol -A 5
```

### Division Before Multiplication (Precision Loss)

```solidity
// VULNERABLE
uint256 result = (amount / totalSupply) * price;  // 0 if amount < totalSupply

// SECURE
uint256 result = (amount * price) / totalSupply;
// Or overflow-safe:
uint256 result = FullMath.mulDiv(amount, price, totalSupply);
```

```bash
rg -n "/ .*\*|\/.*\*" --type sol
```

---

## Post-Cancun EVM Changes

### SELFDESTRUCT (EIP-6780)

After Dencun (March 2024), `SELFDESTRUCT` no longer destroys contract code or clears storage. It only sends the ETH balance. Metamorphic contract patterns are broken.

```bash
rg -n "selfdestruct|SELFDESTRUCT" --type sol
# Flag any use -- likely deprecated pattern
```

### Transient Storage (EIP-1153)

New opcodes `TSTORE`/`TLOAD` -- data persists for one transaction only. Perfect for reentrancy guards.

```solidity
contract TransientReentrancyGuard {
    bytes32 constant LOCK_SLOT = keccak256("reentrancy.lock");

    modifier nonReentrant() {
        assembly {
            if tload(LOCK_SLOT) { revert(0, 0) }
            tstore(LOCK_SLOT, 1)
        }
        _;
        assembly { tstore(LOCK_SLOT, 0) }
    }
    // Gas savings: ~2900 gas vs SSTORE-based (~5000 warm, ~20000 cold)
}
```

```bash
rg -n "tstore|tload|TSTORE|TLOAD" --type sol
```

---

## CREATE2 / CREATE3 Deployment Patterns

```solidity
// CREATE2: address = keccak256(0xff, deployer, salt, keccak256(initCode))
// CREATE3: address depends only on deployer + salt (not initCode)

// SECURITY: If salt is user-controlled, include msg.sender to prevent front-running
bytes32 salt = keccak256(abi.encodePacked(msg.sender, userSalt));
```

```bash
rg -n "CREATE2|create2|CREATE3|create3" --type sol
rg -n "keccak256.*0xff|assembly.*create2" --type sol
```

---

## Low-Level Assembly Pitfalls

```solidity
// PITFALL 1: Returndata bomb -- callee returns huge data, OOG on copy
(bool ok, bytes memory data) = target.call("");  // Copies all returndata

// SECURE: Limit returndata copy in assembly
assembly {
    let ok := call(gas(), target, 0, 0, 0, 0, 0)
    if gt(returndatasize(), 0x40) { revert(0, 0) }
    returndatacopy(0, 0, returndatasize())
}

// PITFALL 2: Dirty high bits in address
assembly { addr := x }  // Upper 96 bits might be non-zero
assembly { addr := and(x, 0xffffffffffffffffffffffffffffffffffffffff) }  // Mask

// PITFALL 3: Forgetting to update free memory pointer
assembly {
    let freePtr := mload(0x40)
    let data := freePtr
    mstore(data, 42)
    mstore(0x40, add(freePtr, 0x20))  // MUST update!
}

// PITFALL 4: No overflow checks in assembly
assembly {
    let result := add(a, b)  // No overflow check!
}
```

```bash
rg -n "assembly\s*\{" --type sol
rg -n "returndatasize|returndatacopy" --type sol
```

---

## Memory vs Calldata vs Storage

```solidity
// Storage = reference, modifies state
function updateUser(User storage user) internal { user.balance = 100; }

// Memory = local copy, does NOT modify state
function readUser(User memory user) internal pure { user.balance = 100; /* copy only! */ }

// Calldata = immutable, cheapest for external read-only params
function sum(uint256[] calldata arr) external pure returns (uint256) { /* no copy */ }
```

---

## Consolidated Quick-Reference Grep Patterns

```bash
# === CRITICAL: Reentrancy ===
rg -n "\.call\{value" --type sol
rg -n "\.call\(" --type sol

# === CRITICAL: Access Control ===
rg -n "selfdestruct|delegatecall" --type sol
rg -n "function.*external|function.*public" --type sol

# === CRITICAL: Oracle ===
rg -n "latestRoundData|getPrice|latestAnswer" --type sol

# === HIGH: Arithmetic ===
rg -n "unchecked" --type sol
rg -n "abi\.encodePacked" --type sol
rg -n "/ .*\*" --type sol

# === HIGH: Proxy/Upgrade ===
rg -n "delegatecall|UUPS|ERC1967|TransparentProxy" --type sol
rg -n "constructor()" --type sol
rg -n "_disableInitializers|initializer\b" --type sol
rg -n "__gap|_gap" --type sol

# === HIGH: Token Handling ===
rg -n "transferFrom|safeTransferFrom" --type sol
rg -n "approve\(" --type sol

# === MEDIUM: Frontrunning ===
rg -n "block.timestamp|block.number" --type sol
rg -n "tx.origin" --type sol
rg -n "amountOutMin|minAmountOut|deadline" --type sol

# === MEDIUM: DoS ===
rg -n "for.*\.length|while.*\.length" --type sol
rg -n "push\(" --type sol

# === LOW: Gas ===
rg -n "string public|string private" --type sol
rg -n "memory.*external" --type sol
```

---

## Exploit-to-Pattern Quick Reference

| Exploit | Loss | Root Cause | Key Detection |
|---------|------|-----------|---------------|
| Euler Finance | $197M | Missing health check after collateral reduction | `balance -=` without `checkLiquidity` |
| Curve/Vyper | $70M+ | Broken reentrancy guard (compiler bug) | Custom `nonReentrant`; state after external call |
| KyberSwap | $47M | Tick boundary edge case | `==` comparisons on `sqrtPrice` |
| Mango Markets | $114M | Oracle manipulation + unrealized PnL | `unrealizedPnl` in collateral; spot oracle without TWAP |
| Beanstalk | $182M | Flash-loan governance (no snapshot) | `balanceOf` in vote weight; no timelock |
| Ronin Bridge | $624M | Compromised multisig keys | Low `threshold`; no withdrawal rate limits |
| Wormhole | $326M | Signature verification bypass | External/user-supplied verifier address |
| Nomad Bridge | $190M | Zero-value trusted root after upgrade | Missing zero checks in initializer |
