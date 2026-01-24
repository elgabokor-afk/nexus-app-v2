
import os
import time
import ccxt
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv(dotenv_path="../.env.local")

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase credentials missing.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Kraken Client (Public data only needed for price checks)
exchange = ccxt.kraken()

print("--- PAPER TRADING BOT INITIALIZED ---")

def get_current_price(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None

def check_new_entries():
    """Checks for new signals to open positions."""
    try:
        # Get recent signals (last 1 hour to ensure we catch active market moves)
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        response = supabase.table("market_signals") \
            .select("*") \
            .gt("timestamp", one_hour_ago) \
            .order("timestamp", desc=True) \
            .execute()
            
        signals = response.data
        
        for signal in signals:
            # Check if we already traded this signal
            existing = supabase.table("paper_positions") \
                .select("id") \
                .eq("signal_id", signal['id']) \
                .execute()
                
            if not existing.data:
                # OPEN POSITION
                print(f"   >>> FOUND SIGNAL: {signal['symbol']} ({signal['signal_type']}) | Conf: {signal['confidence']}%")
                print(f"       Opening Position at {signal['price']}...")
                
                # Simple allocation: $1000 per trade
                quantity = 1000 / signal['price']
                
                # Calculate Bot's SL/TP (Currently simply adopting Signal's, but ready for V3 optimization)
                # In V3, we will modify these based on 'bot_params' history
                bot_sl = signal.get('stop_loss')
                bot_tp = signal.get('take_profit')

                trade_data = {
                    "signal_id": signal['id'],
                    "symbol": signal['symbol'],
                    "entry_price": signal['price'],
                    "quantity": quantity,
                    "status": "OPEN",
                    "confidence_score": signal.get('confidence'),
                    "signal_type": signal.get('signal_type'),
                    "rsi_entry": signal.get('rsi'),
                    "atr_entry": signal.get('atr_value'),
                    # NEW: Track Bot's specific decision
                    "bot_stop_loss": bot_sl,
                    "bot_take_profit": bot_tp
                }
                
                supabase.table("paper_positions").insert(trade_data).execute()
                print(f"--- TRADE OPENED: {signal['symbol']} | SL: {bot_sl} | TP: {bot_tp} ---")
                
    except Exception as e:
        print(f"Error checking entries: {e}")

def monitor_positions():
    """Monitors open positions for SL/TP."""
    try:
        # Get all OPEN positions
        response = supabase.table("paper_positions") \
            .select("*, market_signals(stop_loss, take_profit)") \
            .eq("status", "OPEN") \
            .execute()
            
        positions = response.data
        
        for pos in positions:
            current_price = get_current_price(pos['symbol'])
            if not current_price:
                continue
                
            # Get SL/TP from the associated signal
            # Note: supbase-py nesting might return market_signals as a dict or list
            signal_data = pos['market_signals']
            # Handle potential list wrapper if one-to-many (though here it's foreign key)
            if isinstance(signal_data, list) and len(signal_data) > 0:
                signal_data = signal_data[0]
                
            stop_loss = signal_data.get('stop_loss')
            take_profit = signal_data.get('take_profit')
            
            exit_reason = None
            
            # CHECK EXITS
            if stop_loss and current_price <= stop_loss:
                exit_reason = "STOP_LOSS"
            elif take_profit and current_price >= take_profit:
                exit_reason = "TAKE_PROFIT"
                
            if exit_reason:
                # CLOSE POSITION
                pnl = (current_price - pos['entry_price']) * pos['quantity']
                
                print(f"Closing {pos['symbol']} | Reason: {exit_reason} | PnL: ${pnl:.2f}")
                
                update_data = {
                    "status": "CLOSED",
                    "exit_price": current_price,
                    "exit_reason": exit_reason,
                    "closed_at": datetime.utcnow().isoformat(),
                    "pnl": pnl
                }
                
                supabase.table("paper_positions") \
                    .update(update_data) \
                    .eq("id", pos['id']) \
                    .execute()

    except Exception as e:
        print(f"Error monitoring positions: {e}")

def main():
    while True:
        check_new_entries()
        monitor_positions()
        time.sleep(10) # Run every 10 seconds

if __name__ == "__main__":
    main()
