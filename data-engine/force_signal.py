import os
import time
import json
from supabase import create_client
from dotenv import load_dotenv
from pusher import Pusher

# Load Env
load_dotenv(dotenv_path='.env.local')

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

APP_ID = os.getenv("PUSHER_APP_ID")
KEY = os.getenv("NEXT_PUBLIC_PUSHER_KEY")
SECRET = os.getenv("PUSHER_SECRET")
CLUSTER = os.getenv("NEXT_PUBLIC_PUSHER_CLUSTER")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

pusher_client = Pusher(
    app_id=APP_ID,
    key=KEY,
    secret=SECRET,
    cluster=CLUSTER,
    ssl=True
)

def force_test_signal():
    print("--- FORCING TEST SIGNAL (UI CHECK) ---")
    
    # 1. Create Mock Signal
    symbol = "TEST/USDT"
    price = 99999.99
    
    signal_data = {
        "symbol": symbol,
        "direction": "LONG",
        "entry_price": price,
        "tp_price": price * 1.02,
        "sl_price": price * 0.98,
        "ai_confidence": 99.9,
        "risk_level": "LOW",
        "status": "ACTIVE",
        "rsi": 50.0,
        "atr_value": 100.0,
        "volume_ratio": 2.5,
        "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }
    
    # 2. Insert into DB
    print("1. Inserting into DB...")
    res = supabase.table("signals").insert(signal_data).execute()
    
    if not res.data:
        print("!!! DB INSERT FAILED !!!")
        return
        
    signal_id = res.data[0]['id']
    print(f"   [OK] Signal Saved ID: {signal_id}")
    
    # 3. Trigger Pusher
    print("2. Triggering Pusher...")
    
    # Prepare payload exactly as Frontend expects
    payload = {
        "id": signal_id,
        "symbol": symbol,
        "signal_type": "BUY", # Mapped from LONG
        "price": price,
        "confidence": 99.9,
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "stop_loss": price * 0.98,
        "take_profit": price * 1.02,
        "rsi": 50.0,
        "atr_value": 100.0,
        "volume_ratio": 2.5
    }
    
    pusher_client.trigger('public-signals', 'new-signal', payload)
    print("   [OK] Pusher Event Sent!")
    print("\n>>> CHECK YOUR DASHBOARD NOW. DO YOU SEE 'TEST/USDT'?")

if __name__ == "__main__":
    force_test_signal()
