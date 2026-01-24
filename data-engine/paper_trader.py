
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

# V45: AI Decision Authority
from cosmos_engine import brain

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
            "min_confidence": 90, # User requested 90% strictness
            "trading_fee_pct": 0.0005, # 0.05% per leg (0.1% Round-Trip)
            "strategy_version": 1 # Initial version
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
            # 0. GLOBAL POSITION LIMIT (V12 Risk Guard)
            active_count_resp = supabase.table("paper_positions") \
                .select("id", count="exact") \
                .eq("status", "OPEN") \
                .execute()
            
            active_count = active_count_resp.count or 0
            max_pos = int(params.get('max_open_positions', 5))
            
            if active_count >= max_pos:
                print(f"       [GUARD] Max Positions Reached ({active_count}/{max_pos}). Skipping remaining signals.")
                break

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

                # V22: BALANCE-BASED MARGIN SIZING
                # Use Total Equity for the risk calculation (Fixed Fractional Sizing)
                target_margin = float(wallet['equity']) * account_risk
                
                # But CAP it based on Free Balance (Cash) to avoid over-exposure
                free_balance = float(wallet['balance'])
                # Never use more than 25% of REMAINING cash on a single trade for safety
                max_safe_margin = free_balance * 0.25 
                
                initial_margin = min(target_margin, max_safe_margin)
                
                # Minimum margin check (don't open dust trades)
                if initial_margin < 2.0:
                    print(f"       [SKIPPED] Insufficient Free Balance (${free_balance:.2f}). Required: ${target_margin:.2f}")
                    continue

                # Leveraged Position Size (Notional Value)
                trade_value = initial_margin * leverage
                quantity = trade_value / signal['price']
                
                print(f"       Opening Position: ${trade_value:.2f} ({leverage}x) | Margin: ${initial_margin:.2f} (from ${free_balance:.2f} free)")
                
                
                # V3 LOGIC: ATR Stops
                atr = signal.get('atr_value', 0)
                entry = signal['price']
                
                # V23: FEE BREAK-EVEN CALCULATION
                fee_rate = float(params.get('trading_fee_pct', 0.001))
                # Min break-even price move is approx 2x fee_rate
                min_tp_move = entry * (fee_rate * 2.1) # 2.1x for a small safety buffer
                
                if "BUY" in signal['signal_type']:
                    # Standard ATR TP
                    tp_atr = entry + (atr * float(params['take_profit_atr_mult']))
                    # Ensure TP covers fees + at least a small profit
                    bot_tp = max(tp_atr, entry + min_tp_move)
                    
                    bot_sl = entry - (atr * float(params['stop_loss_atr_mult']))
                    # Liquidation: Entry - (Entry / Leverage) for Longs
                    liq_price = entry - (entry / leverage)
                else:
                    # Standard ATR TP (Short)
                    tp_atr = entry - (atr * float(params['take_profit_atr_mult']))
                    # Ensure TP covers fees
                    bot_tp = min(tp_atr, entry - min_tp_move)
                    
                    bot_sl = entry + (atr * float(params['stop_loss_atr_mult']))
                    # Liquidation: Entry + (Entry / Leverage) for Shorts
                    liq_price = entry + (entry / leverage)

                # 5. V45 TOTAL AI AUTHORITY (BLM Decision Matrix)
                # The AI now evaluates all factors (Trend, Book Imbalance, ML Confidence)
                # and makes the final decision. This replaces several manual filters.
                features = {
                    "price": signal['price'],
                    "rsi_value": signal.get('rsi', 50),
                    "ema_200": signal.get('ema_200', signal['price']),
                    "atr_value": signal.get('atr_value', 0),
                    "macd_line": signal.get('macd', 0),
                    "histogram": signal.get('histogram', 0),
                    "imbalance_ratio": signal.get('imbalance', 0)
                }
                
                should_trade, ai_conf, ai_reason = brain.decide_trade(signal['signal_type'], features)
                
                if not should_trade:
                    print(f"       [SKIPPED] {ai_reason}")
                    continue
                
                print(f"       [AI APPROVED] {ai_reason}")

                # V30: NET-TARGETED TP/SL CALCULATION
                # Target Net Profit = (ATR * TakeProfitMult) * Qty
                # Target Net Loss = (ATR * StopLossMult) * Qty
                atr_val = signal.get('atr_value', 0)
                tp_mult = float(params.get('take_profit_atr_mult', 2.5))
                sl_mult = float(params.get('stop_loss_atr_mult', 1.5))
                
                target_net_profit = (atr_val * tp_mult) * abs(quantity)
                target_net_loss = (atr_val * sl_mult) * abs(quantity)
                
                abs_qty = abs(quantity)
                fee_r = float(params.get('trading_fee_pct', 0.0005))
                
                if "BUY" in signal['signal_type']:
                    # Net-Targeted TP (Solve for Price)
                    # Price = (NetTarget + Entry*Qty*(1+Fee)) / (Qty*(1-Fee))
                    bot_tp = (target_net_profit + price_val * abs_qty * (1 + fee_r)) / (abs_qty * (1 - fee_r))
                    # Net-Targeted SL (Solve for Price where NetPnL = -target_net_loss)
                    bot_sl = (-target_net_loss + price_val * abs_qty * (1 + fee_r)) / (abs_qty * (1 - fee_r))
                    liq_price = price_val - (price_val / leverage)
                else:
                    # Net-Targeted TP (Short)
                    # Price = (Entry*Qty*(1-Fee) - NetTarget) / (Qty*(1+Fee))
                    bot_tp = (price_val * abs_qty * (1 - fee_r) - target_net_profit) / (abs_qty * (1 + fee_r))
                    # Net-Targeted SL (Short)
                    bot_sl = (price_val * abs_qty * (1 - fee_r) + target_net_loss) / (abs_qty * (1 + fee_r))
                    liq_price = price_val + (price_val / leverage)

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
                    "liquidation_price": round(liq_price, 4),
                    "strategy_version": params.get('strategy_version', 1)
                }
                
                supabase.table("paper_positions").insert(trade_data).execute()
                print(f"--- TRADE OPENED: {signal['symbol']} ({leverage}x) | Liq: {liq_price:.2f} ---")
                
    except Exception as e:
        print(f"Error checking entries: {e}")

def monitor_positions():
    """Monitors open positions for SL/TP."""
    try:
        params = get_bot_params()
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
                # V23: NET PROFIT GUARD
                # Check if closing now actually makes money after fees
                raw_pnl = (current_price - pos['entry_price']) * pos['quantity']
                if "SELL" in (pos.get('signal_type') or "BUY"): 
                     raw_pnl = (pos['entry_price'] - current_price) * pos['quantity']
                
                fee_rate = float(params.get('trading_fee_pct', 0.001))
                entry_notion = pos['entry_price'] * abs(pos['quantity'])
                exit_notion = current_price * abs(pos['quantity'])
                total_f = (entry_notion + exit_notion) * fee_rate
                
                if raw_pnl > total_f:
                    exit_reason = "TAKE_PROFIT"
                else:
                    # Not enough profit to cover fees yet. Wait longer!
                    pass
                
            if exit_reason:
                # CLOSE POSITION
                total_fees = 0
                if exit_reason == "LIQUIDATION":
                    # Total Loss of Initial Margin
                    pnl = -float(pos.get('initial_margin') or 0)
                else:
                    # Standard PnL Calculation
                    raw_pnl = (current_price - pos['entry_price']) * pos['quantity']
                    # If SHORT, PnL is inverted (Entry - Exit)
                    if "SELL" in (pos.get('signal_type') or "BUY"): 
                         raw_pnl = (pos['entry_price'] - current_price) * pos['quantity']

                    # V21 LOGIC: ROUND-TRIP FEES
                    # Fee = Notional Value * Fee Rate (e.g. 0.0005 or 0.05% per side)
                    # User requested 0.1% Total Round-Trip.
                    fee_rate = float(params.get('trading_fee_pct', 0.0005))
                    
                    entry_notional = pos['entry_price'] * abs(pos['quantity'])
                    exit_notional = current_price * abs(pos['quantity'])
                    
                    total_fees = (entry_notional + exit_notional) * fee_rate
                    pnl = raw_pnl - total_fees

                print(f"Closing {pos['symbol']} | Reason: {exit_reason} | PnL: ${pnl:.2f} (Fees: ${total_fees:.2f})")
                
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
