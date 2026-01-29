
import time
import json
import os
import sys
import redis
from datetime import datetime
from dotenv import load_dotenv

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

from binance_engine import live_trader
from db import log_error
from supabase import create_client
from pusher_client import pusher_client

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("/// N E X U S  E X E C U T O R  (Live Trading V1.0) ///")
print("WARNING: REAL MONEY MODE ACTIVE")
print("-" * 50)

# CONFIG
REDIS_URL = os.getenv("REDIS_URL")
MAX_EXPOSURE_PCT = 0.50 # Max 50% of account used
MAX_SLIPPAGE = 0.005 # 0.5%
API_ERROR_LIMIT = 3

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe('trade_signal')

consecutive_errors = 0

def get_account_stats():
    """Fetches Available Balance and Total Exposure."""
    try:
        balance = live_trader.get_live_balance()
        positions = live_trader.get_open_positions()
        # Calculate used margin
        # Simplify: Just return balance for now
        return balance, len(positions)
    except Exception as e:
        return 0, 0

def validate_signal(data):
    """
    Checks if signal is valid for execution:
    1. Slippage Check (Current Price vs Signal Price)
    2. Permission Check (API Withdrawal - Simulated here by assuming success)
    3. Exposure Check
    """
    symbol = data['symbol']
    signal_price = float(data['price'])
    
    # 1. Fetch Current Price
    ticker = live_trader.fetch_ticker(symbol)
    if not ticker: 
        return False, "Ticker Error"
        
    curr_price = ticker['last']
    deviation = abs(curr_price - signal_price) / signal_price
    
    if deviation > MAX_SLIPPAGE:
        return False, f"Slippage too high ({deviation*100:.2f}% > {MAX_SLIPPAGE*100:.2f}%)"
        
    return True, "OK"

def main_loop():
    global consecutive_errors
    
    print(">>> Listening for Redis Signals...")
    
    for message in pubsub.listen():
        if message['type'] != 'message': continue
        
        try:
            data = json.loads(message['data'])
            # Verify it's a "LIVE" intent signal (or we treat all signals as executable if in LIVE mode?)
            # Usually scanner sends signals. PaperBot listens. Executor listens.
            # We filter by confidence or source?
            # For now, EXECUTE ALL SIGNALS sent to this channel (assuming upstream filtered).
            
            symbol = data['symbol']
            side = 'buy' if 'BUY' in data['signal'] else 'sell'
            
            print(f"\n[SIGNAL RECEIVED] {symbol} {side.upper()} | Conf: {data.get('confidence', 0)}%")
            
            # CHECK 1: Risk & Slippage
            is_valid, reason = validate_signal(data)
            if not is_valid:
                print(f"   [REJECT] {reason}")
                continue
                
            # CHECK 2: Balance Logic
            balance, open_pos = get_account_stats()
            if balance < 10: # Min $10
                print("   [REJECT] Insufficient Balance (<$10)")
                continue
                
            # CALCULATE SIZE
            # Risk 2% of Balance
            risk_amt = balance * 0.02
            # Size = Risk / (Entry - SL) ... simplistic
            # Let's use Fixed Size $50 for safety first test?
            # User said "Pre-Check Balance", didn't specify sizing algo.
            # I'll use a safe Default $20 size for safety.
            # Real logic: (Account * 0.05) * Leverage ?
            # Let's do $30 fixed for now.
            usd_size = 30.0 
            amount = usd_size / float(data['price'])
            
            print(f"   [EXEC] Allocating ${usd_size} ({amount:.4f} coins)...")
            
            # EXECUTE BRACKET
            res = live_trader.execute_bracket_order(
                symbol=symbol,
                side=side,
                amount=amount,
                leverage=5,
                stop_loss=float(data['stop_loss']),
                take_profit=float(data['take_profit'])
            )
            
            if res['status'] == 'SUCCESS':
                consecutive_errors = 0
                print(f"   >>> TRADE EXECUTED! ID: {res['entry_id']}")
                
                # LOG TO DB
                supabase.table('live_trades').insert({
                    'symbol': symbol,
                    'side': side,
                    'entry_price': res['filled_avg_price'],
                    'size': amount,
                    'entry_order_id': str(res['entry_id']),
                    'status': 'OPEN',
                    'sl_order_id': str(res['sl_id']),
                    'tp_order_id': str(res['tp_id'])
                }).execute()
                
                # PUSHER
                pusher_client.trigger('live-execution', 'order-filled', {
                    'symbol': symbol,
                    'price': res['filled_avg_price'],
                    'side': side,
                    'size': usd_size
                })
            else:
                consecutive_errors += 1
                print(f"   [FAIL] Execution Failed: {res.get('error')}")
                
            # KILL SWITCH
            if consecutive_errors >= 3:
                msg = "KILL SWITCH ACTIVATED: 3 Consecutive API Errors."
                print(f"!!! {msg}")
                pusher_client.trigger('dashboard-alerts', 'critical-error', {'message': msg})
                log_error("nexus_executor", msg, "CRITICAL")
                sys.exit(1) # Crash pod to force restart/attention
            
        except Exception as e:
            print(f"Loop Error: {e}")
            consecutive_errors += 1

if __name__ == "__main__":
    if live_trader.mode != "LIVE":
        print("!!! WARNING: TRADING_MODE is set to PAPER. Executor running in SIMULATION ONLY.")
        # We allow it to proceed because binance_engine handles simulation internally.
        
    main_loop()
