
import os
import time
import asyncio
import json
import logging
from datetime import datetime, timezone
import traceback
from dotenv import load_dotenv

# Load env variables
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [COSMOS WORKER] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Internal Engines
# Import Internal Engines
brain = None
redis_engine = None
scanner_engine = None
macro_brain = None
quant_engine = None
live_trader = None

try:
    from cosmos_engine import brain
except ImportError as e:
    logger.warning(f"Cosmos Brain missing: {e}")

try:
    from redis_engine import redis_engine
except ImportError as e:
    logger.warning(f"Redis Engine missing: {e}")

try:
    from macro_feed import macro_brain
except ImportError as e:
    logger.warning(f"Macro Feed missing: {e}")

try:
    from cosmos_quant import quant_engine
except ImportError as e:
    logger.warning(f"Quant Engine missing: {e}")
    
try:
    from binance_engine import live_trader
except ImportError as e:
    logger.warning(f"Binance Engine missing: {e}")

# Database Setup
from supabase import create_client, Client
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# V310: Global Confidence Fallbacks
min_confidence_threshold = 25
macro_sentiment = "NEUTRAL"
dynamic_pairs = []
last_dynamic_update = 0
last_training_time = 0
last_optimization = 0
worker_started = False

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase credentials missing. Exiting.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Constants
LOOP_INTERVAL = 60 # Seconds

def save_signal_to_db(signal_data):
    """
    Writes the signal to the strictly defined 'public.signals' table.
    Schema: pair, direction, entry_price, tp_price, sl_price, ai_confidence, risk_level, status
    """
    try:
        # Map Engine Dict to SQL Schema
        db_record = {
            "symbol": signal_data.get('symbol'),
            "direction": "LONG" if "BUY" in signal_data.get('signal_type', '') else "SHORT",
            "entry_price": signal_data.get('price'),
            "tp_price": signal_data.get('take_profit'),
            "sl_price": signal_data.get('stop_loss'),
            "ai_confidence": float(signal_data.get('confidence', 0)),
            "risk_level": "HIGH" if float(signal_data.get('confidence', 0)) < 85 else "MID", 
            "status": "ACTIVE",
            "rsi": signal_data.get('rsi'),
            "atr_value": signal_data.get('atr_value'),
            "volume_ratio": signal_data.get('volume_ratio'),
            "created_at": datetime.now(timezone.utc).isoformat()
            # NOTE: entry/tp/sl are still here for backward compatibility during migration
            # They will be removed/nulled after Frontend update.
        }
        
        # 1. Insert into Public Signals (Main ID)
        res = supabase.table("signals").insert(db_record).execute()
        
        if res.data:
            signal_id = res.data[0]['id']
            
            # 2. Insert into VIP Secure Table (The Real Vault)
            vip_record = {
                "signal_id": signal_id,
                "entry_price": signal_data.get('price'),
                "tp_price": signal_data.get('take_profit'),
                "sl_price": signal_data.get('stop_loss'),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            try:
                supabase.table("vip_signal_details").insert(vip_record).execute()
                logger.info(f"   [SECURE] Signal {signal_id} vaulted in VIP table.")
            except Exception as e:
                logger.error(f"Failed to vault VIP details: {e}")

            return signal_id
        return None
    except Exception as e:
        logger.error(f"Failed to save signal DB: {e}")
        return None

def fetch_win_rate():
    """Fetch current Win Rate from the database view."""
    try:
        res = supabase.table("trading_performance").select("win_rate").limit(1).execute()
        if res.data and res.data[0]['win_rate'] is not None:
             return float(res.data[0]['win_rate'])
        return 50.0 # Default if no history
    except Exception as e:
        logger.warning(f"Failed to fetch Win Rate: {e}")
        return 50.0

def main_loop():
    logger.info("--- COSMOS AI WORKER STARTED [RAILWAY MODE] ---")
    
    while True:
        # V3000: HEARTBEAT & STARTUP LOGGING
        # This runs ONCE per loop cycle start (or usually just once if we insert before while)
        # But we want to ensure we log at least once.
        try:
            if not worker_started:
                try:
                    supabase.table("error_logs").insert({
                        "message": "COSMOS WORKER RESTARTED (v3.0)", 
                        "error_level": "INFO", 
                        "service": "COSMOS_WORKER"
                    }).execute()
                    worker_started = True
                    logger.info("   >>> [DB] Logged Startup Event")
                except: pass
                
            # V6: GLOBAL OPTIMIZER (Every 4 Hours)
            # Adjusts Weights & Leverage based on Regime (Volatile vs Ranging)
            if time.time() - last_optimization > 14400: # 4 Hours
                logger.info("   [OPTIMIZER] Running Global Parameter Tuning...")
                try:
                    from optimizer import run_optimization
                    run_optimization()
                    last_optimization = time.time()
                except Exception as opt_e:
                     logger.error(f"Optimizer Failed: {opt_e}")
                     
        except Exception as e:
            logger.error(f"Failed to log startup: {e}")

        try:
            start_time = time.time()
            
            # 1. Fetch Candidates & Scan
            # We import logic from scanner.py to avoid code duplication
            # Assumption: scanner.py functions are stateless enough or valid
            # 1. Fetch Candidates & Scan
            from scanner import fetch_data, analyze_market, analyze_quant_signal, fetch_fear_greed, get_top_vol_pairs, SYMBOLS, PRIORITY_ASSETS
            
            logger.info("Scanning markets...")
            fng_index = fetch_fear_greed()
            
            # V24: Dynamic Asset List Update (Every 30m)
            # We persist this variable outside the loop (using a hack or global if needed, 
            # but here we can just fetch if the variable is empty or time elapsed)
            # Since 'main_loop' is a while loop, we define this outside in a better structure, 
            # but to minimize diff size:
            # V42: RECURSIVE LEARNING LOOP (Every 1 Hour)
            if time.time() - last_training_time > 3600:
                logger.info("   [RECURSIVE AI] Fetching Trade History & Updating Theses (Biases)...")
                try:
                    history = brain.fetch_training_data()
                    brain.update_asset_bias(history.to_dict('records') if not history.empty else [])
                    last_training_time = time.time()
                except Exception as e:
                    logger.error(f"Recursive Training Failed: {e}")

            # V24: Dynamic Asset List Update (Every 30m)
            if time.time() - last_dynamic_update > 1800:
                logger.info("   [DYNAMIC] Updating top volume assets...")
                try:
                    dynamic_pairs = get_top_vol_pairs(limit=10)
                    last_dynamic_update = time.time()
                except Exception as de:
                    logger.error(f"Dynamic Update Failed: {de}")
                    if not dynamic_pairs: dynamic_pairs = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

            # Combine symbols: Priority + Static + Dynamic
            symbols_to_scan = list(set(PRIORITY_ASSETS + SYMBOLS + dynamic_pairs))
            logger.info(f"Scanning {len(symbols_to_scan)} Assets: {symbols_to_scan}")
            
            generated_signals = [] 
            
            for symbol in symbols_to_scan:
                try:
                    # V310: GLOBAL BLACKLIST CHECK
                    from scanner import ASSET_BLACKLIST
                    if any(b in symbol for b in ASSET_BLACKLIST):
                         # logger.info(f"Skipping Blacklisted Asset: {symbol}")
                         continue

                    # Fetch Data (5m and 15m for confluence)
                    df_5m = fetch_data(symbol, timeframe='5m', limit=100)
                    df_15m = fetch_data(symbol, timeframe='15m', limit=100)
                    df_4h = fetch_data(symbol, timeframe='4h', limit=50) # V1400: High Timeframe for Structure
                    
                    techs_5m = analyze_market(df_5m)
                    techs_15m = analyze_market(df_15m)
                    
                    if techs_5m and techs_15m:
                        # Confluence Check
                        ma_15m = techs_15m['ema_200']
                        p_5m = techs_5m['price']
                        trend_15m = "BULLISH" if p_5m > ma_15m else "BEARISH"
                        
                        # V1500: Always broadcast live price to UI during scan
                        redis_engine.publish("live_prices", {
                            "symbol": symbol.upper(),
                            "price": p_5m,
                            "time": int(time.time())
                        })

                        # V3800: PUSHER BROADCAST (Direct to Frontend)
                        try:
                            from pusher_client import pusher_client
                            pusher_client.trigger("public-price-feed", "price-update", {
                                "symbol": symbol.upper(),
                                "price": p_5m,
                                "time": int(time.time())
                            })
                        except Exception as e:
                            logger.warning(f"Failed to broadcast price to Pusher: {e}")
                        
                        # V3300: CRITICAL - Fetch Real-Time Price
                        real_price = p_5m 
                        if live_trader:
                            try:
                                ticker = live_trader.fetch_ticker(symbol)
                                real_price = float(ticker['last']) if ticker and 'last' in ticker else p_5m
                            except Exception as e:
                                pass 

                        # V42: SMC ORDER BLOCK ANALYSIS
                        # Import here to avoid circular dep issues at top level if any
                        from smc_engine import smc_engine
                        smc_data = smc_engine.analyze(df_5m)
                        
                        # AI + Quant Analysis
                        quant_signal = analyze_quant_signal(
                            symbol, 
                            techs_5m, 
                            sentiment_score=fng_index, 
                            df_confluence=df_5m, 
                            df_htf=df_4h,
                            current_price=real_price
                        )
                        
                        if quant_signal:
                            # 15m Trend Filter
                            if "BUY" in quant_signal['signal'] and trend_15m != "BULLISH":
                                continue
                            elif "SELL" in quant_signal['signal'] and trend_15m != "BEARISH":
                                continue
                                
                            # V3400: ORDER FLOW & WHALE CHECK
                            if quant_engine:
                                flow_analysis = quant_engine.analyze_order_flow(symbol)
                                if flow_analysis['valid']:
                                    if "BUY" in quant_signal['signal'] and flow_analysis['sentiment'] == 'BEARISH':
                                        continue
                                    if "SELL" in quant_signal['signal'] and flow_analysis['sentiment'] == 'BULLISH':
                                        continue
                                        
                                    walls = flow_analysis.get('whale_walls', [])
                                    if "BUY" in quant_signal['signal'] and any("SELL_WALL" in w for w in walls):
                                         continue

                                    quant_signal['quant_note'] = f"Flow: {flow_analysis['sentiment']} (Imb: {flow_analysis['imbalance']})"
                                    
                                    # V42: Institutional Context Helper
                                    # Used for the 'Academic Thesis' generation later or simply logging
                                    inst_context = "Institutional Flow Detected"
                            else:
                                quant_signal['quant_note'] = "Quant Engine Offline"

                            # Convert to Worker Signal Format
                            
                            # V5000: NORMALIZE CONFIDENCE
                            raw_conf = quant_signal['confidence']
                            final_conf = raw_conf
                            
                            if "SELL" in quant_signal['signal']:
                                final_conf = 100 - raw_conf
                            
                            # V42: RECURSIVE BIAS APPLICATION (The "Thesis" Multiplier)
                            asset_bias = brain.get_asset_bias(symbol)
                            final_conf_boosted = final_conf * asset_bias
                            
                            # Log significant boosts
                            if asset_bias != 1.0:
                                logger.info(f"   [THESIS] {symbol} Bias {asset_bias:.2f}x applied: {final_conf:.0f}% -> {final_conf_boosted:.0f}%")
                            
                            # V42: SMC BOOST
                            # If Order Block aligns, huge confidence boost
                            smc_boost = 0
                            if "BUY" in quant_signal['signal'] and smc_data.get('ob_bullish'): smc_boost = 15
                            if "SELL" in quant_signal['signal'] and smc_data.get('ob_bearish'): smc_boost = 15
                            
                            if smc_boost > 0:
                                final_conf_boosted += smc_boost
                                logger.info(f"   [SMC] Order Block Detected! Confidence +{smc_boost}%")

                            # Update Payload
                            sig_payload = {
                                "symbol": symbol,
                                "signal_type": quant_signal['signal'],
                                "price": quant_signal['price'],
                                "take_profit": quant_signal['take_profit'],
                                "stop_loss": quant_signal['stop_loss'],
                                "confidence": final_conf_boosted, # Recursive + SMC Enhanced
                                "rsi": quant_signal.get('rsi'),
                                "atr_value": quant_signal.get('atr_value'),
                                "volume_ratio": quant_signal.get('volume_ratio'),
                                # "smc_details": smc_data # Optional: Store in DB if schema supports it
                            }
                            
                            # V1700: Apply Dynamic Threshold
                            # Now using Normalized & Boosted Confidence
                            # The threshold acts as the "Wall Street Gatekeeper"
                            if sig_payload['confidence'] >= (60 + min_confidence_threshold): 
                                 generated_signals.append(sig_payload)
                                 logger.info(f"   >>> SIGNAL FOUND: {symbol} {quant_signal['signal']} (Conf: {sig_payload['confidence']:.0f}%)")
                            else:
                                 pass
                                 # logger.info(f"   [FILTER] Signal {symbol} discarded (Conf {sig_payload['confidence']:.0f}% < {60+min_confidence_threshold}%)")
                
                except Exception as e:
                    logger.error(f"Error scanning {symbol}: {e}")
                    continue
                
                # Tiny sleep to be nice to API
                time.sleep(0.5)

            if not generated_signals:
                logger.info("No signals generated this cycle.")
            
            for sig in generated_signals:
                # 2. Save to DB (Strict Schema)
                sig_id = save_signal_to_db(sig)
                
                if sig_id:
                    sig['id'] = sig_id # Attach DB ID
                    
                    logger.info(f"published signal {sig['symbol']}")

                    # 3. Broadcast to Pusher (Dual Channel Strategy)
                    from pusher_client import pusher_client
                    
                    # Channel 1: Public Signals (Censored for Free Users)
                    public_payload = sig.copy()
                    # If confidence is VERY high, we might show it, but for now we follow strict VIP logic
                    # Censor critical info
                    for key in ['price', 'entry_price', 'take_profit', 'stop_loss', 'tp_price', 'sl_price']:
                         public_payload[key] = None # Nullify for free users
                    
                    pusher_client.trigger("public-signals", "new-signal", public_payload)
                    
                    # Channel 2: VIP Signals (The Full Alpha)
                    # We send the RAW signal data to the private channel
                    pusher_client.trigger("private-vip-signals", "new-signal", sig)

                    # V5000: NEXUS EXECUTOR BRIDGE (Critical for Live Trading)
                    # We must publish to 'trade_signal' for nexus_executor.py to react
                    try:
                        redis_engine.publish("trade_signal", json.dumps({
                            "symbol": sig['symbol'],
                            "signal": sig['signal_type'], # 'BUY' or 'SELL'
                            "price": sig['price'],
                            "take_profit": sig['take_profit'],
                            "stop_loss": sig['stop_loss'],
                            "confidence": sig['confidence'],
                            "timestamp": int(time.time())
                        }))
                        logger.info(f"   [REDIS] >>> Sent Signal {sig['symbol']} to Nexus Executor")
                    except Exception as re:
                        logger.error(f"Failed to publish to Nexus Executor: {re}")

                    # Legacy Redis (Optional: Keep for internal tools/PaperBot if needed)
                    # redis_engine.publish("live_signals", { "type": "NEW_SIGNAL", "data": public_payload })

                    logger.info(f"Published Signal: {sig['symbol']}")

            # V3600: BROADCAST MARKET STATUS (Macro + FNG) for UI Widgets
            try:
                from pusher_client import pusher_client
                status_payload = {
                    "sentiment": macro_sentiment, 
                    "dxy_change": macro_brain.cached_data.get('dxy_change', 0) if macro_brain else 0,
                    "spx_change": macro_brain.cached_data.get('spx_change', 0) if macro_brain else 0,
                    "fng_index": fng_index,
                    "active_sum": len(generated_signals), 
                    "timestamp": int(time.time())
                }
                pusher_client.trigger("public-market-status", "update", status_payload)
            except Exception as e:
                logger.warning(f"   [PUSHER] Failed to broadcast status: {e}")

            # V2700: COSMOS AI AUDITOR INTEGRATION
            try:
                from cosmos_auditor import audit_active_signals
                from cosmos_oracle import run_oracle_step
                
                logger.info("Running AI Signal Audit...")
                audit_active_signals()

                # V3000: Neural Link Activator
                # Randomly pick a priority asset to analyze for the "Thought Stream"
                import random
                target = random.choice(['BTC/USDT', 'ETH/USDT', 'SOL/USDT'])
                logger.info(f"Running Oracle Thought Process on {target}...")
                run_oracle_step(target)

            except Exception as e:
                logger.error(f"Audit/Oracle Cycle Failed: {e}")

            # Sleep remainder of minute
            elapsed = time.time() - start_time
            sleep_time = max(0, LOOP_INTERVAL - elapsed)
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            logger.info("Worker stopped by user.")
            break
        except Exception as e:
            logger.error(f"Critical Worker Error: {e}")
            traceback.print_exc()
            time.sleep(10) # Safety cool-off

if __name__ == "__main__":
    main_loop()
