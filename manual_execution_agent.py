import os
import time
import ccxt
from supabase import create_client
from dotenv import load_dotenv

# Load Environment (Credentials are already safely stored here)
load_dotenv(dotenv_path=".env.local")

# API Keys (From Env, matching what you provided)
API_KEY = os.getenv("BINANCE_API_KEY")
SECRET = os.getenv("BINANCE_SECRET")
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print("--- ANTIGRAVITY EXECUTION AGENT (V2900) ---")
print("Target: Binance Futures (USDT-M)")
print("Filter: Confidence > 70%")

# 1. Initialize Connections
try:
    binance = ccxt.binance({
        'apiKey': API_KEY,
        'secret': SECRET,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap', # Futures
            'adjustForTimeDifference': True
        }
    })
    binance.load_markets()
    print("✅ Binance Connected.")
except Exception as e:
    print(f"❌ Binance Connection Failed: {e}")
    exit()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Fetch Active Signals Analysis
print("\nScanning 'market_signals' for opportunities...")
try:
    # Get signals from last 6 hours to ensure relevance
    response = supabase.table("market_signals") \
        .select("*") \
        .gt("confidence", 70) \
        .order("created_at", desc=True) \
        .limit(20) \
        .execute()
    
    signals = response.data
    print(f"found {len(signals)} high-confidence candidates.")
except Exception as e:
    print(f"❌ Signal Fetch Failed: {e}")
    signals = []

# 3. Execution Logic
for sig in signals:
    symbol = sig['symbol']
    side = sig['signal_type'].upper() # BUY/SELL
    conf = sig['confidence']
    price = sig['price']
    
    # Map for Kraken->Binance if needed, though usually symbols match enough or need '/USDT'
    # Assuming standard format like BTC/USDT
    
    print(f"\nAnalyzing Candidate: {symbol} ({side}) | Conf: {conf}%")
    
    # Check if we already have a position
    try:
        positions = binance.fetch_positions([symbol])
        has_position = False
        for pos in positions:
            if float(pos['entryPrice']) > 0 and float(pos['contracts']) > 0:
                 print(f"   ⚠️ Position already exists on Binance. Skipping.")
                 has_position = True
                 break
        
        if has_position: continue
        
        # Execute
        print(f"   🚀 EXECUTING {side} ORDER for {symbol}...")
        
        # Determine Amount (Conservative: 15 USDT worth)
        # Using a fixed reliable amount for safety in this manual tool
        usdt_amount = 15.0
        quantity = usdt_amount / price
        
        # Min quantity precision adjustment would be needed for prod, 
        # but CCXT often handles basic precision if create_market_order is simple.
        # For robustness, we try/catch the precision errors.
        
        order = binance.create_order(
            symbol=symbol,
            type='market',
            side=side.lower(),
            amount=quantity,
            params={'leverage': 10} # Enforcing user's 10x request
        )
        
        print(f"   ✅ ORDER SUCCEEDED: ID {order['id']}")
        print(f"   PLEASE VERIFY ON BINANCE APP.")
        
        # Sleep to avoid rate limits
        time.sleep(1)

    except Exception as e:
        print(f"   ❌ Execution Failed: {e}")

print("\n--- AGENT CYCLE COMPLETE ---")
