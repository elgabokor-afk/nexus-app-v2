
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
            "default_leverage": 10, # V2500: Upgraded to x10
            "margin_mode": "CROSSED",
            "account_risk_pct": 0.02, # Safe default
            "min_confidence": 80, # V2200: Strict filtering (Was 60)
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
    # V250: DISABLED BY USER REQUEST (Trust Dashboard Signals)
    # if TRADING_MODE != "LIVE": return
    return # Force Disable Reality Check

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
        
        
        # V3210: DAILY TRADE LIMIT
        # We check how many positions were opened since UTC Midnight.
        # User requested 300 limit override
        max_daily = GLOBAL_CONFIG.get('max_daily_positions', 300)
        # Handle case where user might set 0 or None -> Default 300
        if not max_daily: max_daily = 300
        
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        # Count trades opened today
        daily_res = supabase.table("paper_positions") \
            .select("id", count="exact") \
            .gte("created_at", today_start) \
            .execute()
            
        daily_count = daily_res.count if daily_res.count is not None else len(daily_res.data)
        
        if daily_count >= max_daily:
            print(f"   [Limit] DAILY CAP REACHED ({daily_count}/{max_daily} trades today). Engine sleeping until midnight UTC.")
            # We still want to monitor existing positions, so we just return from check_new_entries,
            # NOT exit the script. Monitor logic runs in main loop separately.
            return

        # Get recent signals (last 1 hour)
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        # V500: Strict Schema - Query 'signals' table
        res = supabase.table("signals") \
            .select("*") \
            .gte("created_at", one_hour_ago) \
            .eq("status", "ACTIVE") \
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
            # 1. RSI Check - Removed as AI already confirms confluence in scanner.py
            
            # 2. CONFIDENCE Check (Strict V415)
            # User Requirement: Confidence >= 85
            min_conf = float(params.get('min_confidence', 85))
            signal_conf = float(signal.get('ai_confidence', 0))
            if signal_conf < min_conf:
                 print(f"       [SKIPPED] {signal.get('symbol', '???')} Low Confidence: {signal_conf}% < {min_conf}%")
                 continue

            # V500: Strict Schema - Schema Mapping
            # signals table -> code logic
            # V2403: Fix Key Error (DB renamed to 'symbol')
            signal_symbol = signal.get('symbol', signal.get('pair', 'UNKNOWN'))
            signal_type = signal.get('direction', 'LONG') # LONG or SHORT
            
            # Check duplication
            existing = supabase.table("paper_trades") \
                .select("id") \
                .eq("signal_id", signal['id']) \
                .execute()

            if existing.data:
                # Already traded this signal ID
                continue

            features = {
                "price": float(signal['entry_price'] or 0),
                "rsi_value": 50, # Placeholder
                "confidence": signal_conf
            }
            
            # V415: RISK:REWARD CHECK
            # Must be at least 1:2
            try:
                potential_profit = abs(float(signal.get('tp_price', 0)) - float(signal.get('entry_price', 0)))
                potential_loss = abs(float(signal.get('entry_price', 0)) - float(signal.get('sl_price', 0)))
                
                if potential_loss == 0: 
                    rr_ratio = 0
                else:
                    rr_ratio = potential_profit / potential_loss
                    
                min_rrr = float(params.get('min_rrr', 2.0))
                if rr_ratio < min_rrr:
                    print(f"       [SKIPPED] Bad R:R ({rr_ratio:.2f}) < {min_rrr}. Precision Mode Active.")
                    continue
            except Exception as e:
                print(f"       [R:R CHECK ERROR] {e}")

            # We skip the Brain re-calculation for now (since it's already in DB from Worker)
            # We trust the signal from the DB.
            should_trade = True
            ai_conf = signal_conf / 100.0
            ai_reason = "Executed from Signal DB"
            
            if not should_trade:
                print(f"       [SKIPPED] {ai_reason}")
                continue
            
            print(f"       [AI APPROVED] {ai_reason}")

            # V94: DYNAMIC MARGIN SIZING (Confidence-Based Scaling)
            # Risk Management: Dynamic % of Equity (capped at 5% safety)
            # Use ai_conf from DB
            leverage = int(params.get('max_leverage', 10))
            conf_multiplier = 1.0 # Base
            if ai_conf > 0.8: conf_multiplier = 1.5
            elif ai_conf < 0.6: conf_multiplier = 0.5
            
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
                .eq("symbol", signal_symbol) \
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
                        print(f"       [SKIPPED] Max Asset Exposure reached for {signal_symbol}")
                        continue
                    print(f"       [DIVERSIFICATION] Scaling down to ${target_margin:.2f} for cap safety.")

            initial_margin = min(target_margin, max_safe_margin)
            
            if initial_margin < 2.0:
                print(f"       [SKIPPED] Final Margin too low (${initial_margin:.2f})")
                continue

            # Final Position Values
            trade_value = initial_margin * leverage
            entry = float(signal['entry_price'] or 0)
            quantity = trade_value / entry if entry > 0 else 0
            if signal_type == "SHORT": quantity = -quantity
            
            print(f"       Opening Position: {signal_symbol} ${trade_value:.2f} {scaling_reason} | Margin: ${initial_margin:.2f}")
            
            # V510: SIGNAL FIDELITY (Mirror Mode)
            # User requested EXACT signal following. We prefer signal values over dynamic calculation.
            
            bot_tp = float(signal.get('tp_price', 0) or 0)
            bot_sl = float(signal.get('sl_price', 0) or 0)
            
            if bot_tp > 0 and bot_sl > 0:
                 print(f"       [V510 MIRROR] Using Signal's Native Targets. TP: {bot_tp} | SL: {bot_sl}")
            else:
                # Fallback to standard 2% TP / 1% SL if missing (Shouldn't happen with strict schema)
                bot_tp = entry * 1.02 if signal_type == "LONG" else entry * 0.98
                bot_sl = entry * 0.99 if signal_type == "LONG" else entry * 1.01
                print(f"       [V510 STANDARD] Signal Lacks TP/SL. Using Fixed 2%/1%")
            
            liq_price = entry - (entry / leverage) if signal_type == "LONG" else entry + (entry / leverage)
            binance_side = 'buy' if signal_type == 'LONG' else 'sell'

            # V100: LIVE EXECUTION BRIDGE
            if TRADING_MODE == "LIVE":
                # V2904: Side Sanitization (Backport)
                sanitized_side = binance_side
                
                print(f"   [V480] EXECUTING CROSS-MARGIN ORDER: {sanitized_side.upper()} {abs(quantity)} {signal_symbol} (Auto-Borrow)")
                
                # V3005: Robust Symbol Mapping (Allows Kraken /USD signals to trade on Binance /USDT)
                # We prioritize the engine's internal mapping, but passing clean /USDT helps.
                execution_symbol = signal_symbol.replace("/USD", "/USDT")
                if "USDT" not in execution_symbol and "USD" not in execution_symbol:
                     # Fallback for plain 'BTC' -> 'BTC/USDT' if needed, or leave as is if CCXT handles it
                     if "/" not in execution_symbol: execution_symbol += "/USDT"
                
                live_trader.execute_market_order(execution_symbol, sanitized_side, abs(quantity), leverage=leverage)


            trade_data = {
                "signal_id": signal['id'],
                "symbol": signal_symbol,
                "entry_price": entry,
                "quantity": quantity,
                "status": "OPEN",
                "confidence_score": signal_conf,
                "signal_type": signal_type,
                "rsi_entry": 50, # Placeholder
                "atr_entry": 0, # Placeholder
                "bot_stop_loss": round(bot_sl, 4),
                "bot_take_profit": round(bot_tp, 4),
                # V5 Fields
                "leverage": leverage,
                "margin_mode": params.get('margin_mode', 'CROSSED'),
                "initial_margin": round(initial_margin, 2),
                "liquidation_price": round(liq_price, 4),
                "strategy_version": params.get('strategy_version', 1)
            }
            
            
            # Educational Log for User Clarity
            if binance_side == 'sell':
                print(f"       [INFO] SHORT POSITION: Profit Target ({bot_tp:.4f}) is BELOW Entry ({entry}). This is CORRECT.")
            else:
                print(f"       [INFO] LONG POSITION: Profit Target ({bot_tp:.4f}) is ABOVE Entry ({entry}).")

            # V500: Strict Schema - Write to 'paper_trades'
            # Note: We still keep 'paper_positions' for internal state tracking if needed,
            # but the Requirement says: "El PaperBot leerá estas señales, ejecutará la operación simulada y actualizará el PnL."
            # We will create the record in 'paper_trades' now.

            trade_data_strict = {
                "signal_id": signal['id'],
                "entry_price_executed": entry,
                "exit_price_executed": None,
                "realized_pnl": None,
                "bot_status": "OPEN"
            }

            supabase.table("paper_trades").insert(trade_data_strict).execute()
            print(f"--- PAPER TRADE OPENED: {signal_symbol} ---")

            # Keep legacy table for compatibility with 'monitor_positions' and FRONTEND Dashboard
            # The dashboard listens to 'paper_positions', so this is CRITICAL for UI to work.
            supabase.table("paper_positions").insert(trade_data).execute()
            
            print(f"--- TRADE OPENED: {signal['symbol']} ({leverage}x) | Type: {binance_side.upper()} | Liq: {liq_price:.2f} ---")
            
            # V1100: HA Broadcast to live_positions
            redis_engine.publish("live_positions", {
                "type": "OPEN",
                "data": trade_data
            })

            # V2100: PUSHER BROADCAST (Frontend Live View)
            # Sends instant notification of the trade to the Dashboard
            try:
                from pusher_client import pusher_client
                # We use a public channel for "Paper" trades so the user sees them immediately
                # (Or private if we want to restrict, but user said "yo poderlas ver")
                pusher_client.trigger("public-paper-positions", "position-update", {
                    "type": "OPEN",
                    "data": trade_data
                })
                print(f"       >>> [PUSHER] Broadcasted OPEN position for {signal_symbol}")
            except Exception as e:
                print(f"       [PUSHER ERROR] {e}")
                
    except Exception as e:
        print(f"Error checking entries: {e}")

def monitor_positions():
    """Monitors open positions for SL/TP."""
    try:
        params = get_bot_params()
        # Get all OPEN positions
        response = supabase.table("paper_positions") \
            .select("*, signals!signal_id(tp_price, sl_price)") \
            .eq("status", "OPEN") \
            .execute()
            
        positions = response.data
        
        for pos in positions:
            current_price = get_current_price(pos['symbol'])
            if not current_price:
                continue
                
            # V1500: Broadcast live price for real-time PnL in UI (No DB overhead)
            redis_engine.publish("live_prices", {
                "symbol": pos['symbol'].upper(),
                "price": current_price,
                "time": int(time.time())
            })
                
            # Get SL/TP from the associated signal (New Schema: signals)
            signal_data = pos.get('signals')
            
            # PRO TRADING LOGIC: Use Editable TP/SL from Position
            # This allows user to modify the active trade (Binance Style)
            stop_loss = pos.get('bot_stop_loss')
            take_profit = pos.get('bot_take_profit')
            
            # Fallback to signal if missing
            if stop_loss is None and signal_data:
                 stop_loss = signal_data.get('sl_price')
            if take_profit is None and signal_data:
                 take_profit = signal_data.get('tp_price')
                 
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
                exit_reason = "TAKE_PROFIT"
                
            # V1600: DYNAMIC MANAGEMENT (Trailing Stop & Time Exit)
            
            # V3400: SMART ALGORITHMIC TRAILING (Structure Based)
            # Replaces fixed % trailing with "Market Structure" trailing
            from scanner import fetch_data 
            
            # Logic:
            # 1. Fetch last 15m candles
            # 2. Find lowest low of last 5 candles (Support)
            # 3. If (Support > Current SL) -> Move SL Up via smart_trailing_stop
            
            try:
                df_structure = fetch_data(pos['symbol'], timeframe='15m', limit=10)
                if df_structure is not None and not df_structure.empty:
                    # Identify Structural Support (Lowest Low of last 5 closed candles)
                    recent_lows = df_structure['low'].iloc[-6:-1] # Ignore current open candle
                    structure_support = recent_lows.min()
                    
                    entry_price = float(pos['entry_price'])
                    current_sl = float(pos.get('bot_stop_loss') or 0)
                    
                    # Buffer: 0.2% below support to avoid wick-outs
                    new_sl = structure_support * 0.998 if "BUY" in (pos.get('signal_type') or "BUY") else structure_support * 1.002
                    
                    should_update_sl = False
                    reason = ""
                    
                    quantity = float(pos['quantity'])

                    # LONG LOGIC
                    if quantity > 0:
                        # Only move SL UP, never down
                        # And only if New SL is ABOVE BreakEven (Protect Profit)
                        if new_sl > current_sl and new_sl > entry_price:
                            should_update_sl = True
                            # Verify PnL is positive enough to justify tight trail
                            if current_price > (entry_price * 1.01): # Only active after 1% profit
                                reason = f"Structure Support ({structure_support:.4f})"

                    # SHORT LOGIC
                    elif quantity < 0:
                         # Only move SL DOWN, never up
                         if (current_sl == 0 or new_sl < current_sl) and new_sl < entry_price:
                             should_update_sl = True
                             if current_price < (entry_price * 0.99):
                                 reason = f"Structure Resistance ({structure_support:.4f})"
                    
                    if should_update_sl:
                        print(f"       [SMART TRAILING] Moving SL to {new_sl:.4f} based on {reason}")
                        supabase.table("paper_positions").update({"bot_stop_loss": new_sl}).eq("id", pos['id']).execute()
                        
                        # V2100: Notify Frontend (Optional, but nice to see dots move)
                        redis_engine.publish("live_positions", {
                            "type": "UPDATE",
                            "data": { "id": pos['id'], "bot_stop_loss": new_sl }
                        })

            except Exception as e:
                print(f"       [SMART TRAIL ERROR] {e}")
                    
            # 2. Time-Based Exit (Stagnation)
            try:
                created_at = datetime.fromisoformat(pos['opened_at'].replace('Z', '+00:00'))
                age_hours = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
                
                # If open > 4 hours and PnL < 0.5% (stuck), close it.
                if age_hours > 4 and profit_pct < 0.005:
                     exit_reason = "TIME_EXIT_STAGNATION"
            except Exception as e:
                print(f"       [TIME EXIT] Error: {e}")
                
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
                    margin = pos.get('initial_margin') or (pos['entry_price'] * abs(pos['quantity']) / (pos.get('leverage', 10)))
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

                # V500: Strict Schema - Update 'paper_trades' and 'signals'
                try:
                    # Update paper_trades
                    supabase.table("paper_trades").update({
                        "exit_price_executed": current_price,
                        "realized_pnl": pnl,
                        "bot_status": "CLOSED"
                    }).eq("signal_id", pos['signal_id']).execute()

                    # Update signals
                    supabase.table("signals").update({
                        "status": "CLOSED",
                        "result_pnl": pnl
                    }).eq("id", pos['signal_id']).execute()
                    
                    print(f"   [V500] Sync: Updated paper_trades and signals for Signal {pos['signal_id']}")
                except Exception as e:
                    print(f"   [V500 Error] Failed to sync strict schema: {e}")
                    
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

                # V2100: PUSHER BROADCAST (Closure)
                try:
                    from pusher_client import pusher_client
                    pusher_client.trigger("public-paper-positions", "position-update", {
                        "type": "CLOSED",
                        "data": {
                            "id": pos['id'],
                            "symbol": pos['symbol'],
                            "pnl": pnl,
                            "exit_price": current_price,
                            "exit_reason": exit_reason,
                            "status": "CLOSED" 
                        }
                    })
                    print(f"       >>> [PUSHER] Broadcasted CLOSED position for {pos['symbol']}")
                except Exception as e:
                    print(f"       [PUSHER ERROR] {e}")
                
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
        # Get last 50 closed trades (Excluding Admin Purges)
        res = supabase.table("paper_positions") \
            .select("pnl") \
            .eq("status", "CLOSED") \
            .neq("exit_reason", "FORCE_PURGE_V1500") \
            .neq("exit_reason", "ZOMBIE_AUTO_ARCHIVE") \
            .not_.is_("pnl", "null") \
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
