
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
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=True, socket_connect_timeout=5)
            self.client.ping()
            print(f"   [REDIS] Connected to: {self.redis_url}")
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

redis_engine = RedisEngine()

if __name__ == "__main__":
    # Test publishing
    redis_engine.publish("test_channel", {"status": "operational", "version": "V900"})
    print("Test message published to 'test_channel'")
