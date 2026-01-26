
import os
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from redis_engine import redis_engine
from binance_engine import live_trader
from supabase import create_client, Client

# Load env
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [PRICE FEED] - %(message)s')
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Symbols to watch (Priority Assets + Active Positions)
from scanner import PRIORITY_ASSETS

def get_active_symbols():
    """Fetch symbols from priority list and any symbol with an OPEN position."""
    try:
        symbols = set(PRIORITY_ASSETS)
        
        # Add symbols from active positions
        res = supabase.table("paper_positions").select("symbol").eq("status", "OPEN").execute()
        if res.data:
            for item in res.data:
                symbols.add(item['symbol'])
        
        return list(symbols)
    except Exception as e:
        logger.error(f"Error fetching active symbols: {e}")
        return PRIORITY_ASSETS

def main():
    logger.info("--- NEXUS REAL-TIME PRICE FEED STARTED ---")
    
    # Tick counter to refresh symbol list every 30s
    last_symbol_refresh = 0
    symbols = get_active_symbols()
    
    while True:
        try:
            if time.time() - last_symbol_refresh > 30:
                symbols = get_active_symbols()
                last_symbol_refresh = time.time()
                logger.info(f"Refreshed symbols: {len(symbols)} active.")

            for symbol in symbols:
                try:
                    ticker = live_trader.fetch_ticker(symbol)
                    if ticker and 'last' in ticker:
                        price = ticker['last']
                        # Publish to Redis
                        redis_engine.publish("live_prices", {
                            "symbol": symbol.upper(),
                            "price": price,
                            "time": int(time.time())
                        })
                except Exception as e:
                    logger.error(f"Error fetching ticker for {symbol}: {e}")
                
            # Loop delay (1 second for ultra-responsive UI)
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Global Price Feed Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
