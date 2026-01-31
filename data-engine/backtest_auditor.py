import os
import time
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
import yfinance as yf
from datetime import datetime, timedelta

# Load env variables
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BacktestAuditor")

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase credentials missing.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def audit_signals():
    logger.info("--- STARTING HISTORICAL AUDIT ---")
    
    # 1. Fetch Closed Signals that haven't been audited
    # We check if they exist in signal_audit_history
    try:
        # Get all signals
        res = supabase.table("signals").select("*").order("created_at", desc=True).limit(50).execute()
        signals = res.data
        
        for sig in signals:
            sig_id = sig['id']
            symbol = sig['symbol']
            entry = float(sig['entry_price'] or 0)
            tp = float(sig['tp_price'] or 0)
            sl = float(sig['sl_price'] or 0)
            created_at = sig['created_at'] # ISO String
            
            if entry == 0: continue

            # Check if already audited
            check = supabase.table("signal_audit_history").select("id").eq("signal_id", sig_id).execute()
            if check.data:
                continue # Skip already audited
            
            logger.info(f"Auditing {symbol} (ID: {sig_id})...")
            
            # 2. Fetch Historical Data (Yahoo Finance)
            # Need to convert symbol: BTC/USDT -> BTC-USD
            yf_symbol = symbol.replace("/", "-").replace("USDT", "USD")
            
            # Start date = created_at
            start_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            end_dt = start_dt + timedelta(days=7) # Look ahead 7 days max
            
            df = yf.download(yf_symbol, start=start_dt, end=end_dt, interval="1h", progress=False)
            
            if df.empty:
                logger.warning(f"   No data for {yf_symbol}")
                continue
            
            # 3. Simulate Trade
            outcome = "PENDING"
            exit_price = entry
            max_profit = 0
            max_drawdown = 0
            
            direction = 1 if "LONG" in (sig.get('direction') or "LONG") else -1
            
            for index, row in df.iterrows():
                high = float(row['High'].iloc[0])
                low = float(row['Low'].iloc[0])
                
                # Check Max Profit/Drawdown
                if direction == 1: # LONG
                    current_profit_pct = (high - entry) / entry * 100
                    current_dd_pct = (low - entry) / entry * 100
                    max_profit = max(max_profit, current_profit_pct)
                    max_drawdown = min(max_drawdown, current_dd_pct)
                    
                    if high >= tp:
                        outcome = "WIN"
                        exit_price = tp
                        break
                    if low <= sl:
                        outcome = "LOSS"
                        exit_price = sl
                        break
                        
                else: # SHORT
                    current_profit_pct = (entry - low) / entry * 100
                    current_dd_pct = (entry - high) / entry * 100
                    max_profit = max(max_profit, current_profit_pct)
                    max_drawdown = min(max_drawdown, current_dd_pct)
                    
                    if low <= tp:
                        outcome = "WIN"
                        exit_price = tp
                        break
                    if high >= sl:
                        outcome = "LOSS"
                        exit_price = sl
                        break
            
            # If still pending after 7 days, assume close at last price
            if outcome == "PENDING":
                last_price = float(df['Close'].iloc[-1].iloc[0])
                exit_price = last_price
                # Calculate final PnL
                if direction == 1:
                    pnl = (exit_price - entry) / entry * 100
                else:
                    pnl = (entry - exit_price) / entry * 100
                
                outcome = "WIN" if pnl > 0 else "LOSS"
            
            final_pnl = 0
            if outcome == "WIN":
                final_pnl = abs(exit_price - entry) / entry * 100
            elif outcome == "LOSS":
                final_pnl = -abs(exit_price - entry) / entry * 100
                
            # 4. Save to Audit Table
            audit_record = {
                "signal_id": sig_id,
                "symbol": symbol,
                "signal_type": sig.get('direction', 'LONG'),
                "entry_price": entry,
                "exit_price": exit_price,
                "outcome": outcome,
                "pnl_percent": round(final_pnl, 2),
                "max_drawdown_pct": round(max_drawdown, 2),
                "max_profit_pct": round(max_profit, 2),
                "duration_minutes": 0 # Placeholder
            }
            
            supabase.table("signal_audit_history").insert(audit_record).execute()
            logger.info(f"   Saved Audit: {outcome} ({final_pnl:.2f}%)")
            
            time.sleep(1) # Rate limit

    except Exception as e:
        logger.error(f"Audit loop failed: {e}")

if __name__ == "__main__":
    audit_signals()
