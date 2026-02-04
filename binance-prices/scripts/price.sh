#!/usr/bin/env python3
"""Get price for a specific symbol from Binance."""
import sys
import json
import urllib.request

SYMBOL = (sys.argv[1] if len(sys.argv) > 1 else "BTC").upper()
QUOTE = (sys.argv[2] if len(sys.argv) > 2 else "USDT").upper()

url = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}{QUOTE}"
try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
        price = float(data["price"])
        print(f"{data['symbol']}: ${price:,.2f}")
except Exception as e:
    print(f"{SYMBOL}{QUOTE}: Not found ({e})")
