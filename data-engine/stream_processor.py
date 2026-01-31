import asyncio
import json
import os
import logging
from redis_engine import redis_engine
import websockets
from dotenv import load_dotenv

# Load Env
load_dotenv()

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [HOT LAYER] - %(message)s')
logger = logging.getLogger(__name__)

# Config
BINANCE_WSS = "wss://stream.binance.com:9443/ws"
NOISE_THRESHOLD_USD = 1000 # Ignore trades < $1000 volume

# Assets to Watch (Aggregated Stream)
# Format: btcusdt@trade/ethusdt@trade
WATCH_LIST = ["btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", "adausdt"]
STREAM_STRING = "/".join([f"{s}@trade" for s in WATCH_LIST])
FULL_URL = f"{BINANCE_WSS}/{STREAM_STRING}"

async def process_trade(trade_data):
    """
    Filters noise and pushes significant flow to Redis.
    """
    try:
        # data map: s=symbol, p=price, q=quantity, T=trade_time
        symbol = trade_data['s']
        price = float(trade_data['p'])
        qty = float(trade_data['q'])
        
        volume_usd = price * qty
        
        # 1. NOISE FILTER
        if volume_usd < NOISE_THRESHOLD_USD:
            return # Drop noise
            
        # 2. Redis Publish (Hot Path)
        # We broadcast to 'live_prices' but only significant updates or throttled
        # For simplicity in this demo, we verify filter efficacy
        
        msg = {
            "symbol": symbol,
            "price": price,
            "vol_usd": volume_usd,
            "ts": trade_data['T']
        }
        
        # Use existing Redis Engine
        # Store latest price in RAM Cache (Overwrite)
        redis_engine.set_price(symbol, price)
        
        # Publish Event
        redis_engine.publish("live_trades", msg)
        
    except Exception as e:
        logger.error(f"Processing Error: {e}")

async def connect_stream():
    async with websockets.connect(FULL_URL) as websocket:
        logger.info(f"Connected to Binance Stream: {len(WATCH_LIST)} Assets.")
        
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                await process_trade(data)
            except Exception as e:
                logger.error(f"Stream Error: {e}")
                break

async def main():
    while True:
        try:
            await connect_stream()
        except Exception as e:
            logger.error(f"Connection Lost. Reconnecting in 5s... ({e})")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stream Processor Stopped.")
