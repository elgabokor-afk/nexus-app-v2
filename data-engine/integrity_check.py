
import os
import ccxt
from dotenv import load_dotenv

# Load Env
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

API_KEY = os.getenv("BINANCE_API_KEY")
SECRET = os.getenv("BINANCE_SECRET")
MODE = os.getenv("TRADING_MODE", "UNKNOWN")

print("--- ORACLE INTEGRITY CHECKER (V540) ---")
print(f"1. ENVIRONMENT MODE: {MODE}")
print(f"2. API KEY LOADED: {'YES' if API_KEY else 'NO'}")
print(f"3. SECRET LOADED: {'YES' if SECRET else 'NO'}")

if not API_KEY or not SECRET:
    print("!!! FAIL: Missing Credentials in .env.local")
    exit(1)

print("4. CONNECTING TO BINANCE (Margin)...")

try:
    exchange = ccxt.binance({
        'apiKey': API_KEY,
        'secret': SECRET,
        'options': {'defaultType': 'margin'},
        'enableRateLimit': True
    })
    
    # Test 1: Load Markets
    print("   > Loading Markets...")
    exchange.load_markets()
    print("   > [SUCCESS] Markets Loaded.")
    
    # Test 2: Fetch Balance
    print("   > Fetching Margin Balance...")
    balance = exchange.fetch_balance()
    usdt_free = balance['USDT']['free']
    print(f"   > [SUCCESS] Connection Valid. Free USDT: {usdt_free}")
    
    # Test 3: Check Permissions (if possible, inferred by balance success)
    if exchange.check_required_credentials():
        print("   > [SUCCESS] Credentials Validated.")
    
    print("\n--- ALL SYSTEMS GREEN. INTEGRITY CONFIRMED. ---")

except Exception as e:
    print(f"\n!!! CONNECTION FAILED: {e}")
    print("Possible Causes:")
    print(" - Invalid API Key/Secret")
    print(" - IP Address not whitelisted in Binance")
    print(" - API Key permissions (Enable Margin missing?)")
    print(" - System Time out of sync")
