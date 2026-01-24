
import os
import time
import ccxt
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
from optimizer import run_optimization # V6 Engine
from datetime import datetime, timedelta, timezone

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

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
        # Fallback defaults with V5 support
        return {
            "rsi_buy_threshold": 30, 
            "stop_loss_atr_mult": 1.5, 
            "take_profit_atr_mult": 2.5,
            "default_leverage": 10,
            "margin_mode": "ISOLATED",
            "account_risk_pct": 0.02
        }
    except Exception as e:
        print(f"Error fetching params: {e}")
        return {
            "rsi_buy_threshold": 30, 
            "stop_loss_atr_mult": 1.5, 
            "take_profit_atr_mult": 2.5,
            "default_leverage": 4, # User requested max x4
            "margin_mode": "ISOLATED",
            "account_risk_pct": 0.02, # Safe default
            "min_confidence": 78 # User requested 78%
        }

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
            # 1. RSI Check
            if signal['rsi'] > params['rsi_buy_threshold'] and "BUY" in signal['signal_type']:
                continue 

            # 2. CONFIDENCE Check (New V17)
            min_conf = float(params.get('min_confidence', 75))
            signal_conf = float(signal.get('confidence', 0))
            if signal_conf < min_conf:
                 print(f"       [SKIPPED] {signal['symbol']} Low Confidence: {signal_conf}% < {min_conf}%")
                 continue

            # 3. DIVERSIFICATION Check (One position per Symbol)
            # Check for ANY open position with this symbol
            active_on_symbol = supabase.table("paper_positions") \
                .select("id") \
                .eq("symbol", signal['symbol']) \
                .eq("status", "OPEN") \
                .execute()
                
            if active_on_symbol.data:
                # Already have an open trade for this coin. Diversify!
                continue
                
            # 4. DUPLICATE SIGNAL Check
            existing = supabase.table("paper_positions") \
                .select("id") \
                .eq("signal_id", signal['id']) \
                .execute()
                
            if not existing.data:
                # OPEN POSITION
                print(f"   >>> FOUND SIGNAL: {signal['symbol']} | Conf: {signal_conf}% | RSI: {signal['rsi']}")
                
                # V5 LOGIC: LEVERAGE & MARGIN
                leverage = int(params.get('default_leverage', 10))
                margin_mode = params.get('margin_mode', 'ISOLATED')
                
                # Risk Management: Dynamic % of Equity (capped at 5% safety)
                user_risk = float(params.get('account_risk_pct', 0.02))
                account_risk = min(user_risk, 0.05) # Hard cap at 5%
                
                # SOLVENCY CHECK: Cannot trade if broke
                if float(wallet['equity']) <= 10: 
                    print(f"       [SKIPPED] Insufficient Equity (${wallet['equity']}). Trading Halted.")
                    continue

                initial_margin = float(wallet['equity']) * account_risk
                
                # Leveraged Position Size (Notional Value)
                trade_value = initial_margin * leverage
                quantity = trade_value / signal['price']
                
                print(f"       Opening Position: ${trade_value:.2f} ({leverage}x) | Margin: ${initial_margin:.2f}")
                
                # V3 LOGIC: ATR Stops
                atr = signal.get('atr_value', 0)
                entry = signal['price']
                
                if "BUY" in signal['signal_type']:
                    bot_sl = entry - (atr * float(params['stop_loss_atr_mult']))
                    bot_tp = entry + (atr * float(params['take_profit_atr_mult']))
                    # Liquidation: Entry - (Entry / Leverage) for Longs
                    liq_price = entry - (entry / leverage)
                else:
                    bot_sl = entry + (atr * float(params['stop_loss_atr_mult']))
                    bot_tp = entry - (atr * float(params['take_profit_atr_mult']))
                    # Liquidation: Entry + (Entry / Leverage) for Shorts
                    liq_price = entry + (entry / leverage)

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
                    "bot_stop_loss": round(bot_sl, 4),
                    "bot_take_profit": round(bot_tp, 4),
                    # V5 Fields
                    "leverage": leverage,
                    "margin_mode": margin_mode,
                    "initial_margin": round(initial_margin, 2),
                    "liquidation_price": round(liq_price, 4)
                }
                
                supabase.table("paper_positions").insert(trade_data).execute()
                print(f"--- TRADE OPENED: {signal['symbol']} ({leverage}x) | Liq: {liq_price:.2f} ---")
                
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
                
            # PRO TRADING LOGIC: Use Editable TP/SL from Position
            # This allows user to modify the active trade (Binance Style)
            stop_loss = pos.get('bot_stop_loss')
            take_profit = pos.get('bot_take_profit')
            
            # Fallback to signal if missing (Legacy support)
            if stop_loss is None and signal_data:
                 stop_loss = signal_data.get('stop_loss')
            if take_profit is None and signal_data:
                 take_profit = signal_data.get('take_profit')
                 
            exit_reason = None
            
            # CHECK EXITS
            # CHECK EXITS
            if pos.get('closure_requested'):
                 exit_reason = "MANUAL_MARKET"
            elif pos.get('liquidation_price') and (
                ("BUY" in (pos.get('signal_type') or "BUY") and current_price <= pos['liquidation_price']) or
                ("SELL" in (pos.get('signal_type') or "BUY") and current_price >= pos['liquidation_price'])
            ):
                 exit_reason = "LIQUIDATION"
            elif stop_loss and current_price <= stop_loss:
                exit_reason = "STOP_LOSS"
            elif take_profit and current_price >= take_profit:
                exit_reason = "TAKE_PROFIT"
                
            if exit_reason:
                # CLOSE POSITION
                if exit_reason == "LIQUIDATION":
                    # Total Loss of Initial Margin
                    pnl = -float(pos.get('initial_margin') or 0)
                else:
                    # Standard PnL Calculation
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
                
                # V6: RUN SELF-OPTIMIZATION
                print("   >>> Triggering AI Optimization...")
                run_optimization()

    except Exception as e:
        print(f"Error monitoring positions: {e}")

def main():
    while True:
        check_new_entries()
        monitor_positions()
        time.sleep(10) # Run every 10 seconds

if __name__ == "__main__":
    main()
