# DeFi Protocol-Specific Vulnerability Patterns

Patterns organized by protocol type: AMM/DEX, Lending, Bridge. Each includes vulnerable and secure code, detection heuristics.

---

## AMM / DEX Patterns

### Sandwich Attack / Missing Slippage Protection

**Severity**: HIGH

Attacker front-runs a swap by buying the token (raising price), victim swaps at inflated price, attacker back-runs by selling.

```solidity
// VULNERABLE: No slippage protection
function swap(address tokenIn, uint256 amountIn) external returns (uint256 amountOut) {
    amountOut = getAmountOut(amountIn);
    IERC20(tokenIn).transferFrom(msg.sender, address(this), amountIn);
    IERC20(tokenOut).transfer(msg.sender, amountOut);
}

// SECURE: Minimum output + deadline
function swap(
    address tokenIn,
    uint256 amountIn,
    uint256 amountOutMin,  // Slippage protection
    uint256 deadline        // Prevent stale txs
) external returns (uint256 amountOut) {
    require(block.timestamp <= deadline, "expired");
    amountOut = getAmountOut(amountIn);
    require(amountOut >= amountOutMin, "slippage");
    IERC20(tokenIn).transferFrom(msg.sender, address(this), amountIn);
    IERC20(tokenOut).transfer(msg.sender, amountOut);
}
```

```bash
# Find swaps without slippage protection
rg -n "function swap|function exchange" --type sol
# Verify each has minAmountOut/amountOutMin parameter
rg -n "amountOutMin|minAmountOut|minimumOut|slippage" --type sol
```

### JIT (Just-In-Time) Liquidity

LP adds concentrated liquidity just before a large swap and removes it immediately after, capturing fees without sustained impermanent loss. Extracts value from passive LPs.

**Mitigation**: Require minimum LP duration before fee accrual.

### Price Manipulation via Low-Liquidity Pools

```solidity
// VULNERABLE: Using spot price from a pool as an oracle
function getPrice(address token) external view returns (uint256) {
    (uint112 reserve0, uint112 reserve1,) = pair.getReserves();
    return reserve1 * 1e18 / reserve0;  // Manipulable with flash loans
}

// SECURE: Use Uniswap V3 TWAP or Chainlink
function getPrice(address token) external view returns (uint256) {
    (int24 arithmeticMeanTick,) = OracleLibrary.consult(pool, TWAP_PERIOD);
    return OracleLibrary.getQuoteAtTick(arithmeticMeanTick, 1e18, token0, token1);
}
```

---

## Lending-Specific Patterns

### Oracle Staleness

```solidity
// VULNERABLE: Not checking oracle freshness
function getPrice(address token) external view returns (uint256) {
    (, int256 price,, uint256 updatedAt,) = priceFeed.latestRoundData();
    return uint256(price);  // Could be hours/days old
}

// SECURE: Check staleness, sequencer, and bounds
function getPrice(address token) external view returns (uint256) {
    (uint80 roundId, int256 price,, uint256 updatedAt, uint80 answeredInRound) =
        priceFeed.latestRoundData();

    require(price > 0, "negative price");
    require(updatedAt != 0, "round not complete");
    require(answeredInRound >= roundId, "stale round");
    require(block.timestamp - updatedAt <= STALENESS_THRESHOLD, "stale price");

    // On L2s (Arbitrum, Optimism), also check sequencer uptime
    (, int256 answer,, uint256 startedAt,) = sequencerFeed.latestRoundData();
    require(answer == 0, "sequencer down");
    require(block.timestamp - startedAt > GRACE_PERIOD, "grace period");

    return uint256(price);
}
```

```bash
# Find Chainlink usage without staleness checks
rg -n "latestRoundData" --type sol
rg -n "updatedAt|staleness|STALE|heartbeat" --type sol
# Check for sequencer feed on L2
rg -n "sequencer|SEQUENCER" --type sol
```

### Bad Debt / Liquidation Cascades

```solidity
// VULNERABLE: No bad debt socialization
function liquidate(address borrower, uint256 repayAmount) external {
    uint256 collateralValue = getCollateralValue(borrower);
    uint256 debtValue = getDebtValue(borrower);
    // No mechanism to handle collateralValue < debtValue
}

// SECURE: Bad debt socialization mechanism
function liquidate(address borrower, uint256 repayAmount) external {
    // ... liquidation logic ...
    uint256 remainingDebt = getDebtValue(borrower);
    uint256 remainingCollateral = getCollateralValue(borrower);

    if (remainingCollateral == 0 && remainingDebt > 0) {
        _socializeBadDebt(borrower, remainingDebt);
    }
}

function _socializeBadDebt(address borrower, uint256 badDebt) internal {
    if (insuranceFund >= badDebt) {
        insuranceFund -= badDebt;
    } else {
        uint256 totalDeposits = getTotalDeposits();
        exchangeRate -= (badDebt * 1e18) / totalDeposits;
    }
    _clearDebt(borrower);
}
```

---

## Bridge-Specific Patterns

### Cross-Chain Replay

```solidity
// VULNERABLE: Message doesn't include chain ID
struct Message {
    address sender;
    address recipient;
    uint256 amount;
    uint256 nonce;
    // Missing: sourceChainId, destinationChainId
}

// SECURE: Include chain IDs and use EIP-712 structured data
struct Message {
    uint16 sourceChainId;
    uint16 destinationChainId;
    address sender;
    address recipient;
    uint256 amount;
    uint256 nonce;
}

function processMessage(Message calldata msg, bytes calldata proof) external {
    require(msg.destinationChainId == block.chainid, "wrong chain");
    bytes32 hash = keccak256(abi.encode(
        DOMAIN_SEPARATOR,
        msg.sourceChainId,
        msg.destinationChainId,
        msg.sender,
        msg.recipient,
        msg.amount,
        msg.nonce
    ));
    require(!processedMessages[hash], "already processed");
    processedMessages[hash] = true;
    // ... verify proof and execute
}
```

```bash
# Find bridge message structs without chain IDs
rg -n "struct.*Message|struct.*Payload" --type sol
rg -n "chainId|chainid|block.chainid" --type sol
rg -n "processedMessages|usedNonces|consumed" --type sol
```

---

## MEV Patterns

### Frontrunning Detection

```bash
# Find functions vulnerable to frontrunning
rg -n "function claim|function bid|function buy|function mint" --type sol
# Find missing deadline/slippage
rg -n "amountOutMin|minAmountOut|deadline" --type sol
```

**Mitigation**: Use commit-reveal schemes for high-value operations; don't trust non-finalized blocks for irreversible actions.
