
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
try:
    from cosmos_engine import brain
    from redis_engine import redis_engine
    from scanner import scanner_engine # Hypothetical scanner import, falling back if not found
except ImportError:
    logger.warning("Components missing. Running in Skeleton Mode.")

# Database Setup
from supabase import create_client, Client
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

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
            "pair": signal_data.get('symbol'),
            "direction": "LONG" if "BUY" in signal_data.get('signal_type', '') else "SHORT",
            "entry_price": signal_data.get('price'),
            "tp_price": signal_data.get('take_profit'),
            "sl_price": signal_data.get('stop_loss'),
            "ai_confidence": signal_data.get('confidence'),
            "risk_level": "HIGH" if signal_data.get('confidence', 0) < 85 else "MID", 
            "risk_level": "HIGH" if signal_data.get('confidence', 0) < 85 else "MID", 
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
        try:
            start_time = time.time()
            
            # 1. Fetch Candidates & Scan
            # We import logic from scanner.py to avoid code duplication
            # Assumption: scanner.py functions are stateless enough or valid
            from scanner import fetch_data, analyze_market, analyze_quant_signal, fetch_fear_greed, SYMBOLS, PRIORITY_ASSETS
            
            logger.info("Scanning markets...")
            fng_index = fetch_fear_greed()
            
            # V1700: SELF-OPTIMIZATION LOOP
            # If Win Rate < 50%, we become more conservative (+5% Confidence Required)
            current_win_rate = fetch_win_rate()
            min_confidence_threshold = 0 # Base
            
            if current_win_rate < 50.0:
                min_confidence_threshold = 5
                logger.info(f"   [SELF-OPTIMIZACIÓN] Win Rate ({current_win_rate}%) < 50%. Aumentando exigencia (+5%).")
            else:
                logger.info(f"   [SELF-OPTIMIZACIÓN] Win Rate ({current_win_rate}%) saludable. Exigencia estándar.")
            
            # Combine symbols
            symbols_to_scan = list(set(PRIORITY_ASSETS + SYMBOLS))
            
            generated_signals = [] 
            
            for symbol in symbols_to_scan:
                try:
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
                        
                        # AI + Quant Analysis
                        # V1400: Pass df_4h for Multi-Timeframe Logic
                        quant_signal = analyze_quant_signal(symbol, techs_5m, sentiment_score=fng_index, df_confluence=df_5m, df_htf=df_4h)
                        
                        if quant_signal:
                            # 15m Trend Filter
                            if "BUY" in quant_signal['signal'] and trend_15m != "BULLISH":
                                continue
                            elif "SELL" in quant_signal['signal'] and trend_15m != "BEARISH":
                                continue
                                
                            # Convert to Worker Signal Format
                            # analyze_quant_signal returns keys: signal, confidence, price, take_profit, stop_loss...
                            sig_payload = {
                                "symbol": symbol,
                                "signal_type": quant_signal['signal'],
                                "price": quant_signal['price'],
                                "take_profit": quant_signal['take_profit'],
                                "stop_loss": quant_signal['stop_loss'],
                                "confidence": quant_signal['confidence'],
                                "rsi": quant_signal.get('rsi'),
                                "atr_value": quant_signal.get('atr_value'),
                                "volume_ratio": quant_signal.get('volume_ratio')
                            }
                            
                            # V1700: Apply Dynamic Threshold
                            if sig_payload['confidence'] >= (50 + min_confidence_threshold) or ("STRONG" in sig_payload['signal_type']):
                                 generated_signals.append(sig_payload)
                                 logger.info(f"   >>> SIGNAL FOUND: {symbol} {quant_signal['signal']} (Conf: {sig_payload['confidence']}%)")
                            else:
                                 logger.info(f"   [FILTER] Signal {symbol} discarded by Optimization Threshold (Req: {50+min_confidence_threshold}%)")
                
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
                    
                    # 3. Broadcast to Redis (Sanitized for Security)
                    # V1800: We strip sensitive price data from the broadcast to prevent sniffing.
                    # VIPs must fetch details via Supabase RLS.
                    safe_payload = sig.copy()
                    for key in ['price', 'entry_price', 'take_profit', 'stop_loss', 'tp_price', 'sl_price']:
                        if key in safe_payload:
                            del safe_payload[key]

                    redis_engine.publish("live_signals", {
                        "type": "NEW_SIGNAL",
                        "data": safe_payload
                    })
                    })
                    logger.info(f"Published Signal: {sig['symbol']}")

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
