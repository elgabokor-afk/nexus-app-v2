import time
import os
import ccxt
import pandas as pd
import numpy as np
from supabase import create_client
from dotenv import load_dotenv
from pusher_client import broadcast_signal

# Load Env
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

# Init Supabase
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Init Binance (Public Data Only)
exchange = ccxt.binanceusdm()

def fetch_market_data(symbol, timeframe='5m', limit=50):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def audit_active_signals():
    print("\n--- 🕵️ COSMOS AI AUDITOR START ---")
    
    # 1. Fetch Active Signals
    try:
        response = supabase.table('signals').select('*').eq('status', 'ACTIVE').execute()
        active_signals = response.data
    except Exception as e:
        print(f"Error fetching active signals: {e}")
        return

    if not active_signals:
        print("No active signals to audit.")
        return

    print(f"Auditing {len(active_signals)} active signals...")

    for signal in active_signals:
        symbol = signal['symbol'] # Already fixed to 'symbol'
        direction = signal['direction'] # 'LONG' or 'SHORT'
        entry_price = float(signal['entry_price'])
        current_tp = float(signal['tp_price'])
        current_sl = float(signal['sl_price'])
        sig_id = signal['id']
        
        # 2. Get Live Data
        df = fetch_market_data(symbol, timeframe='5m')
        if df is None: continue
        
        current_price = df['close'].iloc[-1]
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].mean()
        
        df['rsi'] = calculate_rsi(df['close'])
        current_rsi = df['rsi'].iloc[-1]
        
        audit_action = None
        audit_note = None
        new_tp = current_tp
        new_sl = current_sl
        
        # --- AUDIT LOGIC ---
        
        # A. Protect Profits (Breakeven Trigger)
        # If price moved 1% in favor, move SL to entry
        price_change_pct = (current_price - entry_price) / entry_price if direction == 'LONG' else (entry_price - current_price) / entry_price
        
        if price_change_pct > 0.01 and current_sl != entry_price:
             new_sl = entry_price
             audit_action = "RISK_FREE"
             audit_note = "🛡️ AI Safety: Locked Breakeven (Price > 1%)"

        # B. Volume Exhaustion (Tighten TP)
        # If we are profitable but volume is dying (< 50% avg), pull TP closer
        if price_change_pct > 0.005 and current_volume < (avg_volume * 0.5):
            # Move TP 50% closer to current price
            if direction == 'LONG' and current_tp > current_price:
                 suggested_tp = current_price + (current_tp - current_price) * 0.5
                 if suggested_tp < new_tp: # Only tighten
                     new_tp = suggested_tp
                     audit_action = "TAKE_PROFIT_TIGHTEN"
                     audit_note = "⚠️ Volume Drop: Tightening Target"
                     
            elif direction == 'SHORT' and current_tp < current_price:
                 suggested_tp = current_price - (current_price - current_tp) * 0.5
                 if suggested_tp > new_tp: # Only tighten
                     new_tp = suggested_tp
                     audit_action = "TAKE_PROFIT_TIGHTEN"
                     audit_note = "⚠️ Volume Drop: Tightening Target"

        # C. RSI Reversal (Emergency Exit Warning)
        if direction == 'LONG' and current_rsi > 75:
             # Overbought - Dangerous
             audit_action = "WARNING"
             audit_note = "🔥 RSI Overbought (75+): Watch for Exit"
             
        if direction == 'SHORT' and current_rsi < 25:
             audit_action = "WARNING"
             audit_note = "❄️ RSI Oversold (25-): Watch for Exit"

        # --- EXECUTE UPDATE ---
        if audit_action:
            print(f"   [AUDIT] {symbol}: {audit_action} -> {audit_note}")
            
            # DB Update
            try:
                supabase.table('signals').update({
                    "sl_price": new_sl,
                    "tp_price": new_tp,
                    "audit_note": audit_note,
                    "last_audit_ts": time.strftime('%Y-%m-%dT%H:%M:%S%z') # UTC ISO
                }).eq('id', sig_id).execute()
                
                # PUSHER BROADCAST (The "Live" Update)
                update_payload = {
                    "id": sig_id,
                    "symbol": symbol,
                    "type": "UPDATE",
                    "audit_action": audit_action,
                    "audit_note": audit_note,
                    "new_sl": new_sl,
                    "new_tp": new_tp,
                    "timestamp": time.time()
                }
                
                # Send to Public (and VIP implicitly if they listen to Public)
                broadcast_signal('public-signals', 'signal-update', update_payload)
                print(f"      >>> [PUSHER] Sent Update for {symbol}")
                
            except Exception as e:
                print(f"Failed to update signal {sig_id}: {e}")
        else:
            print(f"   [OK] {symbol}: Holding steady. (RSI: {current_rsi:.1f}, Vol Ratio: {current_volume/avg_volume:.2f})")

if __name__ == "__main__":
    audit_active_signals()
