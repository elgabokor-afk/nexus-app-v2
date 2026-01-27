import os
import sys
import time
from dotenv import load_dotenv
import pusher

# Load env vars
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

# Verify keys
PUSHER_APP_ID = os.getenv("PUSHER_APP_ID")
PUSHER_KEY = os.getenv("NEXT_PUBLIC_PUSHER_KEY")
PUSHER_SECRET = os.getenv("PUSHER_SECRET")
PUSHER_CLUSTER = os.getenv("NEXT_PUBLIC_PUSHER_CLUSTER")

if not PUSHER_APP_ID or not PUSHER_KEY:
    print("❌ Error: Pusher credentials missing in .env.local")
    sys.exit(1)

# Init Pusher
pusher_client = pusher.Pusher(
    app_id=PUSHER_APP_ID,
    key=PUSHER_KEY,
    secret=PUSHER_SECRET,
    cluster=PUSHER_CLUSTER,
    ssl=True
)

def send_test_signal():
    print(f"📡 Sending Test Signal to Cluster: {PUSHER_CLUSTER}...")

    # Simulated Signal Data
    signal_data = {
        "id": f"TEST-{int(time.time())}",
        "symbol": "BTC/USDT",
        "signal_type": "BUY",
        "entry_price": 65000.00,
        "price": 65000.00,
        "tp_price": 67000.00,
        "sl_price": 64000.00,
        "stop_loss": 64000.00,
        "take_profit": 67000.00,
        "confidence": 88,
        "rsi": 45.5,
        "atr_value": 120.5,
        "volume_ratio": 2.5,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S")
    }

    # 1. Public Payload (Censored)
    public_payload = signal_data.copy()
    for key in ['price', 'entry_price', 'take_profit', 'stop_loss', 'tp_price', 'sl_price']:
        public_payload[key] = None
    
    pusher_client.trigger("public-signals", "new-signal", public_payload)
    print("✅ Public Signal Sent (Censored)")

    # 2. Private Payload (Full)
    pusher_client.trigger("private-vip-signals", "new-signal", signal_data)
    print("✅ VIP Signal Sent (Full Data)")

if __name__ == "__main__":
    send_test_signal()
