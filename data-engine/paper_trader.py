
import os
import time
import ccxt
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

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

def get_wallet():
    """Fetch current virtual wallet state."""
    try:
        res = supabase.table("bot_wallet").select("*").limit(1).execute()
        if res.data:
            return res.data[0]
        return {"id": 1, "balance": 10000, "equity": 10000}
    except Exception as e:
        print(f"Error fetching wallet: {e}")
        return {"id": 1, "balance": 10000, "equity": 10000}

def update_wallet(pnl):
    """Update wallet equity after a trade close."""
    try:
        wallet = get_wallet()
        new_equity = float(wallet['equity']) + float(pnl)
        new_balance = float(wallet['balance']) + float(pnl) 
        
        # In a Margin model, Balance and Equity move together on Realized PnL
        supabase.table("bot_wallet").update({
            "equity": new_equity, 
            "balance": new_balance,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }).eq("id", wallet['id']).execute()
        
        print(f"   $$$ WALLET UPDATE: Equity ${new_equity:.2f} (PnL: ${pnl:.2f})")
    except Exception as e:
        print(f"Error updating wallet: {e}")

def get_bot_params():
    """Fetch active trading parameters from the Brain."""
    try:
        res = supabase.table("bot_params").select("*").eq("active", "true").limit(1).execute()
        if res.data:
            return res.data[0]
        # Fallback defaults
        return {"rsi_buy_threshold": 30, "stop_loss_atr_mult": 1.5, "take_profit_atr_mult": 2.5}
    except Exception as e:
        print(f"Error fetching params: {e}")
        return {"rsi_buy_threshold": 30, "stop_loss_atr_mult": 1.5, "take_profit_atr_mult": 2.5}

def check_new_entries():
    """Checks for new signals to open positions."""
    try:
        params = get_bot_params()
        wallet = get_wallet()
        
        # Get recent signals (last 1 hour)
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        response = supabase.table("market_signals") \
            .select("*") \
            .gt("timestamp", one_hour_ago) \
            .order("timestamp", desc=True) \
            .execute()
            
        signals = response.data
        
        for signal in signals:
            # V3 LOGIC: Dynamic Filter based on 'bot_params'
            # Only trade if the signal matches our CURRENT learning state
            # (e.g. if we learned to be conservative, we might skip high RSI buys)
            
            # Simple check: If signal RSI is strictly below our Threshold
            if signal['rsi'] > params['rsi_buy_threshold'] and "BUY" in signal['signal_type']:
                continue # Skip signal, too risky for current brain
                
            # Check if we already traded this signal
            existing = supabase.table("paper_positions") \
                .select("id") \
                .eq("signal_id", signal['id']) \
                .execute()
                
            if not existing.data:
                # OPEN POSITION
                print(f"   >>> FOUND SIGNAL: {signal['symbol']} | RSI: {signal['rsi']} (Thresh: {params['rsi_buy_threshold']})")
                
                # V3 LOGIC: Position Sizing = 5% of Equity (Compounding)
                account_risk = 0.05 
                trade_value = float(wallet['equity']) * account_risk
                quantity = trade_value / signal['price']
                
                print(f"       Opening Position: ${trade_value:.2f} ({quantity:.4f} units)")
                
                # V3 LOGIC: Dynamic Exits based on ATR Multipliers from DB
                atr = signal.get('atr_value', 0)
                entry = signal['price']
                
                # Recalculate SL/TP based on *CURRENT* bot params, confusing raw signal values if needed
                # Ideally we trust the signal, but V3 implies the BOT decides.
                # Let's Apply the Multipliers to the Entry Price
                if "BUY" in signal['signal_type']:
                    bot_sl = entry - (atr * float(params['stop_loss_atr_mult']))
                    bot_tp = entry + (atr * float(params['take_profit_atr_mult']))
                else:
                    bot_sl = entry + (atr * float(params['stop_loss_atr_mult']))
                    bot_tp = entry - (atr * float(params['take_profit_atr_mult']))

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
                    "bot_stop_loss": round(bot_sl, 4),
                    "bot_take_profit": round(bot_tp, 4)
                }
                
                supabase.table("paper_positions").insert(trade_data).execute()
                print(f"--- TRADE OPENED: {signal['symbol']} | SL: {bot_sl:.2f} | TP: {bot_tp:.2f} ---")
                
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
                
                # If SHORT, PnL is inverted (Entry - Exit)
                if "SELL" in (pos.get('signal_type') or "BUY"): 
                     pnl = (pos['entry_price'] - current_price) * pos['quantity']

                print(f"Closing {pos['symbol']} | Reason: {exit_reason} | PnL: ${pnl:.2f}")
                
                update_data = {
                    "status": "CLOSED",
                    "exit_price": current_price,
                    "exit_reason": exit_reason,
                    "closed_at": datetime.now(timezone.utc).isoformat(),
                    "pnl": pnl
                }
                
                supabase.table("paper_positions") \
                    .update(update_data) \
                    .eq("id", pos['id']) \
                    .execute()
                    
                # V3: Update Wallet Balance
                update_wallet(pnl)

    except Exception as e:
        print(f"Error monitoring positions: {e}")

def main():
    while True:
        check_new_entries()
        monitor_positions()
        time.sleep(10) # Run every 10 seconds

if __name__ == "__main__":
    main()
