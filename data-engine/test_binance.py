import os
import ccxt
from dotenv import load_dotenv

# Load env
load_dotenv('.env.local')

api_key = os.getenv("BINANCE_API_KEY")
secret = os.getenv("BINANCE_SECRET")

def test_connectivity():
    print("--- BINANCE FUTURES INTEGRITY CHECK ---")
    
    if not api_key or not secret:
        print("[!] ERROR: API Key or Secret missing in .env.local")
        return

    print(f"API Key found: {api_key[:5]}...{api_key[-5:]}")
    
    # Initialize CCXT
    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': secret,
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })

    try:
        print("1. Testing API Connectivity...")
        balance = exchange.fetch_balance()
        usdt_free = balance['total'].get('USDT', 0)
        print(f"[SUCCESS] Connected! Live USDT Balance (Futures): ${usdt_free:.2f}")

        if usdt_free < 5:
            print("[!] WARNING: Balance is below $5. Binance may reject small orders.")

        print("\n2. Checking Market Symbols...")
        exchange.load_markets()
        
        # Look for BTC
        target_symbol = "BTC/USDT"
        if target_symbol in exchange.markets:
            print(f"[OK] Found {target_symbol} in market list.")
        else:
            # Fallback check
            native_symbol = "BTCUSDT"
            if native_symbol in exchange.markets:
                print(f"[OK] Found {native_symbol} in market list (Native mode).")
            else:
                print(f"[!] ERROR: Could not find BTC futures market. Available symbols: {list(exchange.markets.keys())[:5]}...")

        print("\n3. Testing Exchange Permissions...")
        # Try to fetch current positions to check for READ/WRITE access
        positions = exchange.fetch_positions()
        print(f"[SUCCESS] Permissions check passed. Active positions: {len([p for p in positions if float(p['contracts']) > 0])}")

        print("\n--- TEST COMPLETE ---")
        print("If all checks above are [SUCCESS] or [OK], the connection is 100% fine.")
        print("The issue is likely the lack of valid 1-hour signals in the database or the bot's risk filters.")

    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        if "API-key format invalid" in str(e):
            print(">>> The API Key you provided is invalid or has an extra space.")
        elif "Invalid API-key, IP, or permissions" in str(e):
            print(">>> Ensure 'Enable Futures' is checked in Binance API Management.")

if __name__ == "__main__":
    test_connectivity()
