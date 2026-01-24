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
        # POST to /market_signals
        # Prefer=return=representation header tells Supabase to return the created object
        url = f"{client.base_url}/market_signals"
        client.headers.update({"Prefer": "return=representation"})
        
        resp = client.post(url, json=data)
        
        if resp.status_code in [200, 201]:
            result = resp.json()
            if result and len(result) > 0:
                print(f"   >>> DB Insert: {symbol} Signal Saved (ID: {result[0]['id']})")
                return result[0]['id']
            return None
        else:
             print(f"   !!! DB Error: {resp.status_code} - {resp.text}")
             return None

    except Exception as e:
        print(f"   !!! DB Error: {e}")
        return None

def insert_analytics(signal_id, ema_200, rsi_value, atr_value, imbalance_ratio, spread_pct, depth_score, macd_line=0, signal_line=0, histogram=0, ai_score=0, sentiment_score=50):
    if not client or not signal_id:
        return

    data = {
        "signal_id": signal_id,
        "ema_200": ema_200,
        "rsi_value": rsi_value,
        "atr_value": atr_value,
        "imbalance_ratio": imbalance_ratio,
        "spread_pct": spread_pct,
        "order_book_depth_score": depth_score,
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram": histogram,
        "ai_score": ai_score,
        "sentiment_score": sentiment_score
    }
    
    try:
        url = f"{client.base_url}/analytics_signals"
        resp = client.post(url, json=data)
        if resp.status_code in [200, 201]:
             print(f"   >>> DB Analytics: Extended Metrics Saved for Signal #{signal_id}")
        else:
             print(f"   !!! DB Analytics Fail: {resp.status_code} - {resp.text}")
    except Exception as e:
         print(f"   !!! DB Analytics Error: {e}")

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

def get_active_position_count():
    if not client: return 0
    try:
        # Select all OPEN positions
        url = f"{client.base_url}/paper_positions?status=eq.OPEN&select=id"
        resp = client.get(url)
        if resp.status_code == 200:
            return len(resp.json())
        return 999 # Safe fallback if error (stop trading)
    except:
        return 999

def get_active_assets():
    """V80: Fetches the list of active symbols to monitor."""
    if not client: return ["BTC/USD"] # Fallback
    try:
        url = f"{client.base_url}/market_assets?is_active=eq.true&select=symbol"
        resp = client.get(url)
        if resp.status_code == 200:
            return [a['symbol'] for a in resp.json()]
        return ["BTC/USD"]
    except Exception as e:
        print(f"   !!! DB Error (Assets): {e}")
        return ["BTC/USD"]

def insert_oracle_insight(symbol, timeframe, trend, prob, reasoning, technical):
    if not client: return
    data = {
        "symbol": symbol,
        "timeframe": timeframe,
        "trend_status": trend,
        "ai_probability": prob,
        "reasoning": reasoning,
        "technical_context": technical
    }
    try:
        url = f"{client.base_url}/oracle_insights"
        client.post(url, json=data)
    except Exception as e:
        print(f"   !!! Oracle DB Error: {e}")

def get_latest_oracle_insight(symbol):
    """Fetches the most recent 1m analysis for a symbol."""
    if not client: return None
    try:
        url = f"{client.base_url}/oracle_insights?symbol=eq.{symbol}&order=timestamp.desc&limit=1"
        resp = client.get(url)
        if resp.status_code == 200 and resp.json():
            return resp.json()[0]
        return None
    except Exception as e:
        print(f"   !!! Database Error (Oracle Fetch): {e}")
        return None

def sync_model_metadata(version, accuracy, samples, features):
    """V71: Syncs local model performance to the hosted DB for Vercel/Railway awareness."""
    if not client: return
    data = {
        "version_tag": version,
        "accuracy": float(accuracy),
        "samples_trained": int(samples),
        "features_used": features,
        "last_bootstrap_at": datetime.now(timezone.utc).isoformat(),
        "active": True
    }
    try:
        url = f"{client.base_url}/ai_model_registry"
        # Since we only want one active row usually, we can either append or upsert.
        # For simplicity and history, we append.
        client.post(url, json=data)
        print(f"   >>> Neural Link: Accuracy ({accuracy*100:.1f}%) synced to Railway/Vercel.")
    except Exception as e:
        print(f"   !!! Neural Link Error: {e}")

def get_last_trade_time():
    if not client: return None
    try:
        url = f"{client.base_url}/paper_positions?order=opened_at.desc&limit=1"
        resp = client.get(url)
        if resp.status_code == 200 and resp.json():
            return resp.json()[0]['opened_at'] 
        return None
    except:
        return None
