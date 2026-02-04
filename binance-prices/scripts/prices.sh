#!/bin/bash
# Get prices for multiple symbols
# Usage: ./prices.sh [SYMBOL1 SYMBOL2 ...]
# Example: ./prices.sh btc eth sol

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -eq 0 ]; then
  # Default: top 10 by volume
  SYMBOLS=("BTC" "ETH" "SOL" "BNB" "XRP" "ADA" "DOGE" "MATIC" "DOT" "LTC")
else
  SYMBOLS=("$@")
fi

for sym in "${SYMBOLS[@]}"; do
  "$SCRIPT_DIR/price.sh" "$sym"
done
