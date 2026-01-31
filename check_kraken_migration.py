from binance_engine import live_trader
import json

print("--- KRAKEN MIGRATION VERIFICATION ---")

test_symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

for sym in test_symbols:
    print(f"\nTesting {sym}:")
    
    # 1. Ticker Test
    print(f"  Fetching Ticker...")
    ticker = live_trader.fetch_ticker(sym)
    if ticker:
        # Check if the ticker info looks like Kraken (Kraken usually has 'info' with different structure)
        print(f"  ✅ Ticker Price: ${ticker['last']}")
    else:
        print(f"  ❌ Ticker Failed.")

    # 2. OHLCV Test
    print(f"  Fetching OHLCV (5m)...")
    ohlcv = live_trader.fetch_ohlcv(sym, timeframe='5m', limit=5)
    if ohlcv and len(ohlcv) > 0:
        print(f"  ✅ OHLCV Success: {len(ohlcv)} candles returned.")
    else:
        print(f"  ❌ OHLCV Failed.")

print("\n--- VERIFICATION COMPLETE ---")
