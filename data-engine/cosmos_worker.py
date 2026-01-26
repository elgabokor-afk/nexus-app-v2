
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
            "status": "ACTIVE",
            "rsi": signal_data.get('rsi'),
            "atr_value": signal_data.get('atr_value'),
            "volume_ratio": signal_data.get('volume_ratio'),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        res = supabase.table("signals").insert(db_record).execute()
        
        # Return the generated ID
        if res.data:
            return res.data[0]['id']
        return None
    except Exception as e:
        logger.error(f"Failed to save signal DB: {e}")
        return None

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
            
            # Combine symbols
            symbols_to_scan = list(set(PRIORITY_ASSETS + SYMBOLS))
            
            generated_signals = [] 
            
            for symbol in symbols_to_scan:
                try:
                    # Fetch Data (5m and 15m for confluence)
                    df_5m = fetch_data(symbol, timeframe='5m', limit=100)
                    df_15m = fetch_data(symbol, timeframe='15m', limit=100)
                    
                    techs_5m = analyze_market(df_5m)
                    techs_15m = analyze_market(df_15m)
                    
                    if techs_5m and techs_15m:
                        # Confluence Check
                        ma_15m = techs_15m['ema_200']
                        p_5m = techs_5m['price']
                        trend_15m = "BULLISH" if p_5m > ma_15m else "BEARISH"
                        
                        # AI + Quant Analysis
                        quant_signal = analyze_quant_signal(symbol, techs_5m, sentiment_score=fng_index, df_confluence=df_5m)
                        
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
                            generated_signals.append(sig_payload)
                            logger.info(f"   >>> SIGNAL FOUND: {symbol} {quant_signal['signal']}")
                
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
                    
                    # 3. Broadcast to Redis (Live Frontend Update)
                    redis_engine.publish("live_signals", {
                        "type": "NEW_SIGNAL",
                        "data": sig
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
