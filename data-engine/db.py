import os
import asyncio
import requests
from dotenv import load_dotenv

# Load env from parent directory
load_dotenv(dotenv_path='../.env.local')

url: str = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

client = None

if url and key:
    # Construct the REST endpoint directly for Postgrest
    # Supabase URL format: https://xyz.supabase.co
    # Postgrest endpoint: https://xyz.supabase.co/rest/v1
    base_url = f"{url}/rest/v1"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    # We can use simple requests or the postgrest-py lib.
    # Actually, requests is easiest and most robust without build tools.
    import requests
    client = requests.Session()
    client.headers.update(headers)
    client.base_url = base_url

def insert_signal(symbol, price, rsi, signal_type, confidence, stop_loss=0, take_profit=0, atr_value=0, volume_ratio=0):
    if not client:
        return
    
    data = {
        "symbol": symbol,
        "price": price,
        "rsi": rsi,
        "signal_type": signal_type,
        "confidence": confidence,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "atr_value": atr_value,
        "volume_ratio": volume_ratio
    }
    
    try:
        # POST to /market_signals
        url = f"{client.base_url}/market_signals"
        resp = client.post(url, json=data)
        if resp.status_code in [200, 201]:
            print(f"   >>> DB Insert: {symbol} Signal Saved.")
        else:
             print(f"   !!! DB Error: {resp.status_code} - {resp.text}")

    except Exception as e:
        print(f"   !!! DB Error: {e}")

def log_error(service, message, error_level="ERROR", stack_trace=None, metadata=None):
    """ Centralized logging to Supabase for remote monitoring """
    if not client:
        return
    
    data = {
        "service": service,
        "message": str(message),
        "error_level": error_level,
        "stack_trace": stack_trace,
        "metadata": metadata
    }
    
    try:
        url = f"{client.base_url}/error_logs"
        resp = client.post(url, json=data)
        if resp.status_code not in [200, 201]:
             print(f"   !!! Log Error Fail: {resp.status_code}")
    except Exception as e:
        print(f"   !!! Logging Failed: {e}")
