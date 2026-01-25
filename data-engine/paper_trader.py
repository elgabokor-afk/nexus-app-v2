
import os
import time
import ccxt
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
from optimizer import run_optimization # V6 Engine
from datetime import datetime, timedelta, timezone
import json # V405
from redis_engine import redis_engine # V1100: HA Broadcasts

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

# V301: GLOBAL ASSET BLACKLIST
ASSET_BLACKLIST = ['PEPE', 'PEPE/USDT', 'PEPE/USD']

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase credentials missing.")
    exit(1)

# V405: GLOBAL CONFIG LOCKDOWN (Dependency-Free JSON)
config_path = os.path.join(parent_dir, "config", "conf_global.json")
GLOBAL_CONFIG = {}
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        GLOBAL_CONFIG = json.load(f) or {}

PAPER_TRADE_ENABLED = GLOBAL_CONFIG.get("paper_trade_enabled", True)
print(f"--- V402 CONFIG: paper_trade_enabled={PAPER_TRADE_ENABLED} ---")
if not PAPER_TRADE_ENABLED:
    print("!!! MASTER SWITCH: Paper Trading is DISABLED. Engine restricted to LIVE path only. !!!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# V100: Database & AI Oracle Integration
from db import get_latest_oracle_insight
from cosmos_engine import brain
from binance_engine import live_trader

print("--- BINANCE EXECUTION & DATA ENGINE ACTIVE (V310) ---")

TRADING_MODE = os.getenv("TRADING_MODE", "PAPER").upper()
# V460: Force LIVE mode if specified in Env, ignoring JSON conflicts
if TRADING_MODE == "LIVE":
    PAPER_TRADE_ENABLED = False 
    print("--- [V402 OVERRIDE] TRADING_MODE is LIVE. Disabling Paper Trade safely. ---")

print(f"--- NEXUS TRADING ENGINE INITIALIZED [MODE: {TRADING_MODE}] ---")

def get_current_price(symbol):
    """V310: Use Binance for price data. V404: Early exit for blacklist."""
    try:
        if any(b in symbol.upper() for b in ASSET_BLACKLIST):
            return None
            
        ticker = live_trader.fetch_ticker(symbol)
        if ticker:
            return ticker['last']
        return None
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None

def get_wallet():
    """Fetch active wallet state (Simulated or Real)."""
    if TRADING_MODE == "LIVE":
        try:
            real_balance = live_trader.get_live_balance()
            # In LIVE mode, Equity = Balance (simplified for Futures margin)
            return {"id": 999, "balance": real_balance, "equity": real_balance}
        except:
             return {"id": 999, "balance": 0, "equity": 0}

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

from telegram_utils import TelegramAlerts
tg = TelegramAlerts() # V600

def get_bot_params():
    """Fetch active trading parameters from the Brain."""
    try:
        res = supabase.table("bot_params").select("*").eq("active", "true").limit(1).execute()
        if res.data:
            return res.data[0]
        # Fallback defaults with V5 support
        return {
            "rsi_buy_threshold": 70, # V470: Aggressive (Was 30)
            "stop_loss_atr_mult": 1.5, 
            "take_profit_atr_mult": 2.5,
            "default_leverage": 10,
            "margin_mode": "CROSSED",
            "account_risk_pct": 0.02
        }
    except Exception as e:
        print(f"Error fetching params: {e}")
        return {
            "rsi_buy_threshold": 70, # V470: Aggressive (Was 30)
            "stop_loss_atr_mult": 1.5, 
            "take_profit_atr_mult": 2.5,
            "default_leverage": 4, # User requested max x4
            "margin_mode": "CROSSED",
            "account_risk_pct": 0.02, # Safe default
            "min_confidence": 60, # V470: Aggressive (Was 90)
            "trading_fee_pct": 0.0005, # 0.05% per leg (0.1% Round-Trip)
            "strategy_version": 1 # Initial version
        }

def reconcile_positions():
    """ADOPT ORPHANED TRADES (V121): Sync DB with Real Binance Positions."""
    if TRADING_MODE != "LIVE": return

    print("--- [V121] RECONCILING POSITIONS WITH BINANCE ---")
    real_positions = live_trader.get_open_positions()
    
    for pos in real_positions:
        symbol = pos['symbol']
        contracts = float(pos['contracts'])
        side = pos['side'] # 'long' or 'short'
        entry_price = float(pos.get('entryPrice', 0))
        if entry_price == 0:
            # Fallback for Margin: Use current market price as proxy for entry
            entry_price = get_current_price(symbol) or 0
        unrealized_pnl = float(pos['unrealizedPnl'])
        
        # Check if DB knows about this position
        db_pos = supabase.table("paper_positions") \
            .select("id") \
            .eq("symbol", symbol) \
            .eq("status", "OPEN") \
            .execute()
            
        if not db_pos.data:
            print(f"   >>> FOUND GHOST POSITION: {symbol} ({side}) {contracts} contracts")
            print(f"   >>> ADOPTING into Database...")
            
            # Create "Adopted" Record
            clean_side = "BUY" if side == 'long' else "SELL"
            
            adopted_data = {
                "signal_id": 9999, # Placeholder for adopted trades
                "symbol": symbol,
                "entry_price": entry_price,
                "quantity": contracts if side == 'long' else -contracts,
                "status": "OPEN",
                "confidence_score": 50,
                "signal_type": f"ADOPTED_{clean_side}",
                "rsi_entry": 50,
                "atr_entry": 0,
                # Safe Defaults for Adopted Trades
                "bot_stop_loss": entry_price * 0.95 if side == 'long' else entry_price * 1.05,
                "bot_take_profit": entry_price * 1.05 if side == 'long' else entry_price * 0.95,
                "leverage": int(pos.get('leverage', 1)),
                "margin_mode": "CROSSED",
                "initial_margin": float(pos.get('initialMargin', contracts * entry_price)),
                "liquidation_price": float(pos.get('liquidationPrice', 0)),
                "strategy_version": 121
            }
            try:
                supabase.table("paper_positions").insert(adopted_data).execute()
                print("   [SUCCESS] Position Adopted.")
            except Exception as e:
                print(f"   [ERROR] Failed to adopt {symbol}: {e}")
        else:
            print(f"   [OK] {symbol} is tracked.")

def archive_zombies():
    """V250: Automatically archive stale 'OPEN' records created > 24h ago."""
    print("--- [V250] SEARCHING FOR ZOMBIE POSITIONS ---")
    try:
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        
        # Mark as CLOSED with reason STALE
        res = supabase.table("paper_positions") \
            .update({
                "status": "CLOSED", 
                "exit_reason": "ZOMBIE_AUTO_ARCHIVE", 
                "closed_at": datetime.now(timezone.utc).isoformat()
            }) \
            .eq("status", "OPEN") \
            .lt("opened_at", yesterday) \
            .execute()
            
        count = len(res.data) if res.data else 0
        if count > 0:
            print(f"   [V250 SUCCESS] Archived {count} stale trades.")
        else:
            print("   [V250] No zombies found.")
    except Exception as e:
        print(f"   [V250 ERROR] Could not archive zombies: {e}")

def sync_live_status():
    """V145: REAL-TIME SYNC & LEARNING (Detect External Closures/Liqs)"""
    if TRADING_MODE != "LIVE": return

    try:
        # 1. Get Live Positions
        live_positions = live_trader.get_open_positions()
        live_symbols = [p['symbol'] for p in live_positions]
        
        # 2. Get Local OPEN Positions
        response = supabase.table("paper_positions") \
            .select("*") \
            .eq("status", "OPEN") \
            .execute()
            
        local_positions = response.data
        
        for local_pos in local_positions:
            # Check if local position is missing from Binance
            if local_pos['symbol'] not in live_symbols:
                print(f"   [V145] EXTERNAL CLOSURE DETECTED: {local_pos['symbol']}")
                
                # It's gone! Likely Liquidation or Manual Close.
                # Mark as CLOSED in DB so AI learns from it.
                current_price = get_current_price(local_pos['symbol'])
                if not current_price: continue
                
                # Calculate approximate PnL based on current price
                # (Not perfect but better than missing data)
                entry = float(local_pos['entry_price'])
                qty = float(local_pos['quantity'])
                
                raw_pnl = (current_price - entry) * qty
                if "SELL" in local_pos['signal_type']:
                    raw_pnl = (entry - current_price) * qty
                    
                print(f"   >>> Recording External Result: PnL ${raw_pnl:.2f}")
                
                supabase.table("paper_positions").update({
                    "status": "CLOSED",
                    "exit_reason": "EXTERNAL_LIQ", # Assessing it as Liq/Manual
                    "exit_price": current_price,
                    "closed_at": datetime.now(timezone.utc).isoformat(),
                    "pnl": raw_pnl
                }).eq("id", local_pos['id']).execute()
                
                # Trigger Learning
                update_wallet(raw_pnl)
                print("   >>> Triggering Immediate Retraining...")
                run_optimization()

    except Exception as e:
        print(f"   [V145] Sync Error: {e}")

def check_new_entries():
    """Checks for new signals to open positions."""
    try:
        params = get_bot_params()
        top_assets = None # V170: Initialize to avoid NameError
        # V130: STANDARDIZED FEE (0.075%)
        # Covers 0.05% Exchange Fee + 0.025% Slippage Buffer
        params['trading_fee_pct'] = 0.00075 
        
        wallet = get_wallet()

        # V135: LIVE BALANCE SYNC & SURVIVAL MODE (<$50)
        is_survival = False
        if TRADING_MODE == "LIVE":
            try:
                live_bal = live_trader.get_live_balance()
                if live_bal > 0:
                     # Update local wallet tracking to match reality
                     wallet['equity'] = live_bal
                     wallet['balance'] = live_bal
                     print(f"   [V135] Synced Real Equity: ${live_bal:.2f}")
                
                if float(wallet['equity']) < 50:
                    is_survival = True
                    print(f"   [SURVIVAL MODE] Equity ${wallet['equity']} < $50. ACTIVATING V420 AGGRESSIVE PIVOT.")
                    # V420: AGGRESSIVE OVERRIDES
                    params['min_confidence'] = 70 # Balanced Aggression
                    params['max_open_positions'] = 5 # Increased from 2
                    params['default_leverage'] = 5 # Increased from 2

                    # V170: ASSET PRUNING (Top 5 Only)
                    top_assets = brain.get_top_performing_assets(limit=5)
                    if top_assets:
                        print(f"   [V170] PEFORMANCE PRUNING ACTIVE. Focus assets: {', '.join(top_assets)}")
                    
            except Exception as e:
                print(f"   [V135] Sync Error: {e}")
        
        # Get recent signals (last 1 hour)
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        res = supabase.table("market_signals") \
            .select("*") \
            .gte("timestamp", one_hour_ago) \
            .execute()
        
        signals = res.data
        if not signals:
            return

        for signal in signals:
            # V414: Global Asset Freedom - Removed old V300/V170 restrictive gating
            # 0. GLOBAL POSITION LIMIT (V250 Reality Check)
            if TRADING_MODE == "LIVE":
                # LIVE Mode: The source of truth is THE EXCHANGE, not the DB zombies.
                real_positions = live_trader.get_open_positions()
                active_count = len(real_positions)
                print(f"   [V250 REALITY CHECK] Binance has {active_count} active positions.")
            else:
                # PAPER Mode: Focus on recent trades to ignore historical artifacts
                yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
                active_count_resp = supabase.table("paper_positions") \
                    .select("id", count="exact") \
                    .eq("status", "OPEN") \
                    .gte("opened_at", yesterday) \
                    .execute()
                active_count = active_count_resp.count or 0
            
            max_pos = int(params.get('max_open_positions', 5))
            
            if active_count >= max_pos:
                if TRADING_MODE == "LIVE":
                    print(f"   [!!!] BLOCKED: You have {active_count} REAL positions in Binance. Limit reached.")
                else:
                    print(f"   [!!!] BLOCKED: You have {active_count} RECENT paper positions. Limit reached.")
                break

            # V3 LOGIC: Dynamic Filter based on 'bot_params'
            # 1. RSI Check
            if signal['rsi'] > params['rsi_buy_threshold'] and "BUY" in signal['signal_type']:
                print(f"       [SKIPPED] {signal['symbol']} High RSI: {signal['rsi']} > {params['rsi_buy_threshold']}")
                continue 

            # 2. CONFIDENCE Check (New V17)
            min_conf = float(params.get('min_confidence', 40))
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
                # V421: AGGRESSIVE STACKING UNLOCK
                # We allow stacking if max positions haven't been reached
                # Just warn, but DO NOT CONTINUE (do not skip)
                print(f"       [V421 STACKING] Adding another {signal['symbol']} position (Aggressive Mode).")
                # continue (REMOVED to allow stacking)
                
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
                
                # 3. V45/V50 TOTAL AI AUTHORITY (BLM + Oracle Gatekeeper)
                oracle_insight = get_latest_oracle_insight(signal['symbol'])
                
                features = {
                    "price": signal['price'],
                    "rsi_value": signal.get('rsi', 50),
                    "ema_200": signal.get('ema_200', signal['price']),
                    "atr_value": signal.get('atr_value', 0),
                    "macd_line": signal.get('macd', 0),
                    "histogram": signal.get('histogram', 0),
                    "imbalance_ratio": signal.get('imbalance', 0)
                }
                
                should_trade, ai_conf, ai_reason = brain.decide_trade(
                    signal['signal_type'], 
                    features, 
                    oracle_insight=oracle_insight,
                    min_conf=(min_conf / 100.0)
                )
                
                if not should_trade:
                    print(f"       [SKIPPED] {ai_reason}")
                    continue
                
                print(f"       [AI APPROVED] {ai_reason}")

                # V94: DYNAMIC MARGIN SIZING (Confidence-Based Scaling)
                # Risk Management: Dynamic % of Equity (capped at 5% safety)
                user_risk = float(params.get('account_risk_pct', 0.02))
                base_account_risk = min(user_risk, 0.05) 
                
                # Confidence Multiplier:
                # Ultra High Conf (>95%) -> 2.0x | High Conf (90-95%) -> 1.0x | Lower Confluence (<90%) -> 0.5x
                conf_multiplier = 1.0
                if ai_conf >= 0.95:
                    conf_multiplier = 2.0
                elif ai_conf < 0.90:
                    conf_multiplier = 0.5
                
                scaling_reason = f"({conf_multiplier}x Scaled)" if conf_multiplier != 1.0 else " (Standard)"
                
                # Solvency Check
                equity = float(wallet['equity'])
                balance = float(wallet['balance'])
                
                # V215: MARGIN LEVEL GUARD (Risk Ratio Health Check)
                # V402: Enforce LIVE check based on Master Switch
                is_live_execution = (TRADING_MODE == "LIVE") and (not PAPER_TRADE_ENABLED)
                
                if is_live_execution:
                    margin_level = live_trader.get_margin_level()
                    print(f"       [V215 MARGIN GUARD] Current Risk Ratio: {margin_level:.2f} (Safe Target: 1.5+)")
                    if margin_level < 1.5:
                        print(f"       [SKIPPED] Margin Level {margin_level:.2f} too low. Trading Halted to prevent debt spiral.")
                        continue

                if equity <= 10: 
                    print(f"       [SKIPPED] Insufficient Equity (${equity}). Trading Halted.")
                    continue

                # Target Margin Calculation
                # V400: SAFETY LAUNCH SIZE ($11 Minimum per Binance requirements)
                target_margin = 11.0
                scaling_reason = " (V400 Launch $11)"
                
                # V135: SURVIVAL OVERRIDE
                if is_survival:
                    # In survival, we keep the smart sizing to ensure we grow the small account
                    print(f"       [SURVIVAL] Using smart margin ${target_margin:.2f}")
                
                # V80: MULTI-ASSET DIVERSIFICATION (15% Cap per Symbol)
                # V240: Disable this cap for fixed $15 margin mode on micro-accounts
                max_asset_exposure = equity * 0.40 # Increase cap to 40% to allow $15 on $40 account
                
                # Free Balance Protection (Never use more than 50% of free balance for $15 orders)
                max_safe_margin = balance * 0.50 
                
                # Check current exposure for this symbol
                existing_asset_pos = supabase.table("paper_positions") \
                    .select("initial_margin") \
                    .eq("symbol", signal['symbol']) \
                    .eq("status", "OPEN") \
                    .execute()
                
                current_exposure = sum([float(p['initial_margin'] or 0) for p in existing_asset_pos.data])
                if current_exposure + target_margin > max_asset_exposure:
                    # Allow one $15 position even if it hits the cap
                    if current_exposure == 0:
                        pass # Allow the first $15 trade
                    else:
                        target_margin = max(0, max_asset_exposure - current_exposure)
                        if target_margin < 2.0:
                            print(f"       [SKIPPED] Max Asset Exposure reached for {signal['symbol']}")
                            continue
                        print(f"       [DIVERSIFICATION] Scaling down to ${target_margin:.2f} for cap safety.")

                initial_margin = min(target_margin, max_safe_margin)
                
                if initial_margin < 2.0:
                    print(f"       [SKIPPED] Final Margin too low (${initial_margin:.2f})")
                    continue

                # Final Position Values
                trade_value = initial_margin * leverage
                quantity = trade_value / signal['price']
                entry = signal['price']
                
                print(f"       Opening Position: {signal['symbol']} ${trade_value:.2f} {scaling_reason} | Margin: ${initial_margin:.2f}")
                
                # V510: SIGNAL FIDELITY (Mirror Mode)
                # User requested EXACT signal following. We prefer signal values over dynamic calculation.
                
                signal_tp = float(signal.get('take_profit', 0) or 0)
                signal_sl = float(signal.get('stop_loss', 0) or 0)
                
                if signal_tp > 0 and signal_sl > 0:
                     print(f"       [V510 MIRROR] Using Signal's Native Targets. TP: {signal_tp} | SL: {signal_sl}")
                     # Pre-calculate multipliers for logging, but we will use the prices directly
                     tp_mult = 0 
                     sl_mult = 0
                else:
                    # Fallback to standard multipliers (Disable V300 Vol-Adapt to be consistent)
                    tp_mult = 2.0 
                    sl_mult = 1.0
                    print(f"       [V510 STANDARD] Signal lacks TP/SL. Using Fixed Multipliers: TP(2.0x) SL(1.0x)")

                target_net_profit = (atr_val * tp_mult) * abs(quantity)
                target_net_loss = (atr_val * sl_mult) * abs(quantity)
                
                # V155/V185: HARD LOSS CAP
                if is_survival:
                    max_allowed_loss = 0.30 # V185: Increased for Breathing Room
                    if target_net_loss > max_allowed_loss:
                        target_net_loss = max_allowed_loss
                        print(f"       [V185] HARD LOSS CAP: Protected risk at ${max_allowed_loss}")
                
                abs_qty = abs(quantity)
                fee_r = float(params.get('trading_fee_pct', 0.0005))
                
                if "BUY" in signal['signal_type']:
                    if signal_tp > 0:
                        bot_tp = signal_tp
                        bot_sl = signal_sl
                    else:
                        bot_tp = (target_net_profit + entry * abs_qty * (1 + fee_r)) / (abs_qty * (1 - fee_r))
                        bot_sl = (-target_net_loss + entry * abs_qty * (1 + fee_r)) / (abs_qty * (1 - fee_r))
                        
                    liq_price = entry - (entry / leverage)
                    binance_side = 'buy'
                else:
                    if signal_tp > 0:
                        bot_tp = signal_tp
                        bot_sl = signal_sl
                    else:
                        bot_tp = (entry * abs_qty * (1 - fee_r) - target_net_profit) / (abs_qty * (1 + fee_r))
                        bot_sl = (entry * abs_qty * (1 - fee_r) + target_net_loss) / (abs_qty * (1 + fee_r))
                        
                    liq_price = entry + (entry / leverage)
                    binance_side = 'sell'

                # V100: LIVE EXECUTION BRIDGE
                if TRADING_MODE == "LIVE":
                    print(f"   [V480] EXECUTING CROSS-MARGIN ORDER: {binance_side.upper()} {abs_qty} {signal['symbol']} (Auto-Borrow)")
                    # Note: Symbol mapping might be needed if Supabase uses different format than Binance
                    # Binance usually expects BTCUSDT (futures)
                    # V180: Strict Binance Futures Symbol Mapping (e.g. BTC/USD -> BTCUSDT)
                    raw_base = signal['symbol'].split('/')[0]
                    binance_pair = f"{raw_base}USDT"
                    
                    live_trader.execute_market_order(binance_pair, binance_side, abs_qty, leverage=leverage)


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
                    "margin_mode": params.get('margin_mode', 'CROSSED'),
                    "initial_margin": round(initial_margin, 2),
                    "liquidation_price": round(liq_price, 4),
                    "strategy_version": params.get('strategy_version', 1)
                }
                
                supabase.table("paper_positions").insert(trade_data).execute()
                print(f"--- TRADE OPENED: {signal['symbol']} ({leverage}x) | Liq: {liq_price:.2f} ---")
                
                # V1100: HA Broadcast to live_positions
                redis_engine.publish("live_positions", {
                    "type": "OPEN",
                    "data": trade_data
                })
                
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
                
            # V300: STAGNATION PRUNING
            # If trade > 4 hours and at a loss, close it to free margin.
            try:
                created_at = datetime.fromisoformat(pos['opened_at'].replace('Z', '+00:00'))
                age = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
                raw_pnl = (current_price - pos['entry_price']) * pos['quantity']
                if "SELL" in (pos.get('signal_type') or "BUY"): 
                    raw_pnl = (pos['entry_price'] - current_price) * pos['quantity']
                
                if age > 4 and raw_pnl < 0:
                    exit_reason = "STAGNATION_PRUNE"
            except Exception as e:
                print(f"       [STAGNATION] Error calculating age: {e}")

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
                
                # V1100: HA Broadcast closure
                redis_engine.publish("live_positions", {
                    "type": "CLOSED",
                    "data": {
                        "id": pos['id'],
                        "symbol": pos['symbol'],
                        "pnl": pnl,
                        "exit_price": current_price,
                        "exit_reason": exit_reason
                    }
                })
                
                # V6: RUN SELF-OPTIMIZATION
                print("   >>> Triggering AI Optimization...")
                run_optimization()

    except Exception as e:
        print(f"Error monitoring positions: {e}")

def check_live_go_signal():
    """
    V600: Convergence Metric.
    Checks if the last 50 Paper Trades have a Win Rate > 60%.
    If so, notifies the user via Telegram to switch to LIVE.
    """
    try:
        # Get last 50 closed trades
        res = supabase.table("paper_positions") \
            .select("pnl") \
            .eq("status", "CLOSED") \
            .order("closed_at", desc=True) \
            .limit(50) \
            .execute()
            
        trades = res.data
        if not trades or len(trades) < 50:
            return
            
        wins = [t for t in trades if float(t.get('pnl', 0)) > 0]
        win_rate = (len(wins) / len(trades)) * 100
        
        print(f"   [V600 MONITOR] Current Training Win Rate: {win_rate:.1f}% ({len(wins)}/50)")
        
        if win_rate >= 60:
            # Check if we already notified recently to avoid spam (e.g. within 24h)
            # For simplicity, we just send it if the threshold is met
            msg = f"🏆 COSMOS AI SIGNAL: TRAINING GOAL REACHED!\n\n" \
                  f"El Win Rate en las últimas 50 operaciones simuladas es del {win_rate:.1f}%.\n" \
                  f"Cosmos ha superado el umbral del 60% y está listo para operar en Binance Futures REAL.\n\n" \
                  f"🚀 Sugerencia: Cambia TRADING_MODE=LIVE en tu .env para iniciar."
            tg.send_msg(msg)
            print("   [V600] Threshold reached! Telegram notification sent.")
            
    except Exception as e:
        print(f"Error checking go signal: {e}")

def main():
    print("--- NEXUS PAPER TRADER STARTED ---")
    
    # V121: Sync Orphaned Positions on Startup
    reconcile_positions()
    
    # V250: Clean up stale DB records to prevent memory/logic issues
    archive_zombies()
    
    while True:
        # V145: Check for external closures first
        sync_live_status()
        
        check_new_entries()
        
        # V600: Periodic Metrics Check
        check_live_go_signal()
        monitor_positions()
        time.sleep(10) # Run every 10 seconds

if __name__ == "__main__":
    main()
