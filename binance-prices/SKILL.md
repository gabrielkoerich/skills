---
name: binance-prices
description: Fetch cryptocurrency prices from Binance public API (no API key required). Use when user asks for BTC, ETH, SOL, or any crypto price from Binance.
homepage: https://github.com/binance/binance-spot-api-docs
---

# Binance Prices

Fetch real-time cryptocurrency prices from Binance public API (no authentication needed).

## Commands

| Command | Usage |
|---------|-------|
| Single price | `scripts/price.sh <SYMBOL> [QUOTE]` |
| Multiple prices | `scripts/prices.sh [SYMBOL1 SYMBOL2 ...]` |

## Examples

```bash
# Bitcoin price in USDT
./scripts/price.sh btc

# Ethereum price in USDT
./scripts/price.sh eth

# Solana price in BUSD
./scripts/price.sh sol busd

# Multiple prices
./scripts/prices.sh btc eth sol

# Custom quotes: BTC in ETH, ETH in BTC
./scripts/price.sh btc eth
./scripts/price.sh eth btc
```

## Supported Quotes

- USDT (default)
- BTC
- ETH
- BUSD

## Output

```
BTCUSDT: $43,234.56
ETHUSDT: $2,345.67
```

## Notes

- Uses public Binance API - no rate limits for basic queries
- Returns real-time prices from Binance spot market
- All prices are in the quote currency (USDT/BTC/ETH/BUSD)
