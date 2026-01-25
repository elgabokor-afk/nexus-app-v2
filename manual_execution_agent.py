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
            'adjustForTimeDifference': True,
            'recvWindow': 60000 # V2901: Max tolerance for clock drift
        }
    })
    
    # V2901: Force Time Sync
    offset = binance.load_time_difference()
    print(f"✅ Binance Connected. Time Offset: {offset}ms")
except Exception as e:
    print(f"❌ Binance Connection Failed: {e}")
    exit()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Fetch Active Signals Analysis
print("\nScanning 'market_signals' for opportunities...")
try:
    response = supabase.table("market_signals") \
        .select("*") \
        .gt("confidence", 70) \
        .order("timestamp", desc=True) \
        .limit(20) \
        .execute()
    
    signals = response.data
    print(f"found {len(signals)} high-confidence candidates.")
except Exception as e:
    print(f"❌ Signal Fetch Failed: {e}")
    signals = []

# 3. Execution Logic
for sig in signals:
    symbol = sig['symbol'] # V2905: Fixed Scope Error
    raw_side = sig['signal_type'].upper()
    side = "BUY" if "BUY" in raw_side else "SELL" if "SELL" in raw_side else None
    
    if not side:
        print(f"   ⚠️ Unknown Signal Type: {raw_side}. Skipping.")
        continue
    
    conf = sig['confidence']
    price = sig['price']
    
    # V2903: Fix Symbol Mapping (Kraken USD -> Binance USDT) gives access to Linear Futures
    # If we pass 'LTC/USD', Binance thinks it's Inverse Futures (Contract size 1). 
    # We want USDT-M (Linear), so we ensure '/USDT'.
    if "/USD" in symbol and "/USDT" not in symbol:
        symbol = symbol.replace("/USD", "/USDT")
        print(f"   🔄 Mapped to {symbol} (USDT-M)")

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
        usdt_amount = 15.0
        raw_quantity = usdt_amount / price
        
        # V2903: Precision Sanitization
        quantity = binance.amount_to_precision(symbol, raw_quantity)
        
        order = binance.create_order(
            symbol=symbol,
            type='market',
             side=side.lower(),
            amount=float(quantity), # Ensure native float
            params={'leverage': 10} # Enforcing user's 10x request
        )
        
        print(f"   ✅ ORDER SUCCEEDED: ID {order['id']}")
        print(f"   PLEASE VERIFY ON BINANCE APP.")
        
        # Sleep to avoid rate limits
        time.sleep(1)

    except Exception as e:
        print(f"   ❌ Execution Failed: {e}")

print("\n--- AGENT CYCLE COMPLETE ---")
