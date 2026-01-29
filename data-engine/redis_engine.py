
import os
import redis
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load env from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

class RedisEngine:
    def __init__(self):
        # V1102: Robust Railway Redis Discovery
        # Railway creates different vars depending on internal/public access
        self.redis_url = os.getenv("REDIS_URL") or os.getenv("REDIS_PRIVATE_URL") or os.getenv("REDIS_PUBLIC_URL")
        
        if not self.redis_url:
            # Try legacy host/port/password composition
            host = os.getenv("REDISHOST")
            port = os.getenv("REDISPORT")
            user = os.getenv("REDISUSER", "default")
            pw = os.getenv("REDISPASSWORD")
            if host and port and pw:
                self.redis_url = f"redis://{user}:{pw}@{host}:{port}"
                print(f"   [REDIS] Composer URL detected: redis://***:***@{host}:{port}")
            else:
                self.redis_url = "redis://localhost:6379"
                print("   [REDIS] No Railway Vars found. Localhost fallback selected.")
        else:
             print(f"   [REDIS] Auto-detected URL: {self.redis_url[:15]}...")
        # Try primary connection
        try:
            print(f"   [REDIS] Attempting connect to: {self.redis_url.split('@')[-1] if '@' in self.redis_url else 'LOCALHOST'}")
            
            # ATTEMPT 1: Standard
            try:
                self.client = redis.from_url(self.redis_url, decode_responses=True, socket_connect_timeout=3)
                self.client.ping()
                print(f"   [REDIS] Connected Successfully (Standard)!")
            except Exception as e:
                print(f"   [REDIS] Standard connection failed ({e}). Retrying with SSL strict=False...")
                # ATTEMPT 2: SSL Relaxed (For Public Proxy)
                self.client = redis.from_url(self.redis_url, decode_responses=True, socket_connect_timeout=3, ssl_cert_reqs=None)
                self.client.ping()
                print(f"   [REDIS] Connected Successfully (SSL Relaxed)!")

        except Exception as e:
            # V1501: Enhanced Diagnostics for Internal vs External
            if ".railway.internal" in self.redis_url:
                print(f"   [REDIS] CRITICAL: You are trying to use an INTERNAL Railway URL from OUTSIDE Railway.")
                print(f"   [REDIS] FIX: In your .env.local / Vercel, change REDIS_URL to the PUBLIC connection string.")
            
            print(f"   [REDIS] Connection Failed ({e}). Switching to OFFLINE MODE.")
            self.client = None

    def publish(self, channel, data):
        """Publish message to a specific channel."""
        if not self.client:
            print(f"   [REDIS] Skip Publish on {channel}: Client not connected.")
            return False
        try:
            # Ensure data is serializable (handle datetime if needed)
            def serializer(obj):
                if isinstance(obj, (datetime, pd.Timestamp)):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")

            message = json.dumps(data, default=serializer)
            self.client.publish(channel, message)
            print(f"   [REDIS] Broadcast on {channel}: {len(message)} bytes.")
            return True
        except Exception as e:
            print(f"   [REDIS] Publish Error on {channel}: {e}")
            return False

    def subscribe(self, channels):
        """Generator that yields messages from subscribed channels."""
        if not self.client:
            return
        
        pubsub = self.client.pubsub()
        pubsub.subscribe(channels)
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                yield message['channel'], json.loads(message['data'])

    def set_price(self, symbol, price):
        """V1000: Cache Price for high-speed read."""
        if not self.client: return
        try:
            # TTL 60s (Prices update fast)
            self.client.setex(f"price:{symbol}", 60, str(price))
        except Exception as e:
            print(f"   [REDIS CACHE FAIL] {e}")

    def get_price(self, symbol):
        """V1000: Read Price from RAM."""
        if not self.client: return None
        try:
            price = self.client.get(f"price:{symbol}")
            return float(price) if price else None
        except:
            return None

    def set_liquidity(self, symbol, bid_vol, ask_vol):
        """V1000: Cache Order Book Depth."""
        if not self.client: return
        try:
            data = json.dumps({"bid": bid_vol, "ask": ask_vol})
            self.client.setex(f"liquidity:{symbol}", 60, data)
        except: pass

    def get_liquidity(self, symbol):
        """Returns dict {bid, ask} or None."""
        if not self.client: return None
        try:
            data = self.client.get(f"liquidity:{symbol}")
            return json.loads(data) if data else None
        except: return None

    # --- Metrics for Admin Dashboard ---
    def incr_counter(self, metric_name):
        if not self.client: return
        self.client.incr(f"stats:{metric_name}")

    def get_counter(self, metric_name):
        if not self.client: return 0
        val = self.client.get(f"stats:{metric_name}")
        return int(val) if val else 0

redis_engine = RedisEngine()

if __name__ == "__main__":
    # Test publishing
    redis_engine.publish("test_channel", {"status": "operational", "version": "V900"})
    print("Test message published to 'test_channel'")
