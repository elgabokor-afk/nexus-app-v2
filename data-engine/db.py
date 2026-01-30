import os
import json
import asyncio
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# Robust Path Resolution for .env.local
current_file_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_file_dir)
env_path = os.path.join(parent_dir, '.env.local')
load_dotenv(dotenv_path=env_path)

url: str = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print(f"!!! [DB INIT ERROR] Missing credentials in {env_path}")
    print(f"    URL: {'Found' if url else 'Missing'} | Key: {'Found' if key else 'Missing'}")

client = None

if url and key:
    base_url = f"{url}/rest/v1"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    client = requests.Session()
    client.headers.update(headers)
    client.base_url = base_url
    print(f"   [DB INIT] Supabase Client Initialized: {url}")

import threading
import queue
import time

class SupabaseBatchWriter:
    def __init__(self, flush_interval=0.5, batch_size=10):
        self.queue = queue.Queue()
        self.flush_interval = flush_interval
        self.batch_size = batch_size
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def add_to_batch(self, table, data):
        self.queue.put((table, data))

    def _worker(self):
        while not self.stop_event.is_set():
            batch = []
            start_time = time.time()
            
            # Collect batch
            while len(batch) < self.batch_size and (time.time() - start_time) < self.flush_interval:
                try:
                    item = self.queue.get(timeout=0.1)
                    batch.append(item)
                except queue.Empty:
                    break
            
            if batch:
                # Group by table
                grouped = {}
                for table, data in batch:
                    if table not in grouped: grouped[table] = []
                    grouped[table].append(data)
                
                # Flush to Supabase
                for table, items in grouped.items():
                    try:
                        url = f"{client.base_url}/{table}"
                        # Simple POST for multiple items is supported by Supabase (array of objects)
                        client.post(url, json=items)
                    except Exception as e:
                        print(f"   [DB BATCH ERROR] {e}")
            
            time.sleep(0.01)

# V1100: HA PRO LAYER
# Live data goes to Redis instantly.
# Legal/Historical sync to Supabase every 30 seconds to minimize I/O and costs.
batch_writer = SupabaseBatchWriter(flush_interval=30.0, batch_size=50)

def insert_signal(symbol, price, rsi, signal_type, confidence, stop_loss=0, take_profit=0, atr_value=0, volume_ratio=0, academic_thesis_id=None, nli_safety_score=1.0, dex_force_score=0, whale_sentiment_score=0, statistical_p_value=1.0):
    if not client:
        print("!!! [DB ERROR] Insert attempted but client NOT initialized.")
        return None
    
    # 1. Map to DB Schema (Signals V2)
    db_data = {
        "symbol": symbol,
        "direction": "LONG" if "BUY" in str(signal_type).upper() else "SHORT",
        "entry_price": price,
        "tp_price": take_profit,
        "sl_price": stop_loss,
        "ai_confidence": confidence,
        "risk_level": "HIGH" if confidence < 85 else "MID",
        "status": "ACTIVE",
        "rsi": rsi,
        "atr_value": atr_value,
        "volume_ratio": volume_ratio,
        "academic_thesis_id": academic_thesis_id,
        "statistical_p_value": statistical_p_value,
        "nli_safety_score": nli_safety_score,
        "dex_force_score": dex_force_score,
        "whale_sentiment_score": whale_sentiment_score,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        # 2. INSTANT BROADCAST TO REDIS (Latency < 10ms)
        # Standardized Payload for nexus_executor.py
        redis_payload = {
            "symbol": symbol,
            "signal": signal_type.upper(),
            "price": price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "confidence": confidence,
            "timestamp": int(time.time())
        }
        redis_engine.publish("trade_signal", json.dumps(redis_payload))

        # 3. IMMEDIATE INSERT TO SUPABASE (No batching for signals)
        url = f"{client.base_url}/signals"
        headers = client.headers.copy()
        headers["Prefer"] = "return=representation"
        resp = client.post(url, json=db_data, headers=headers)
        
        if resp.status_code in [201, 200] and resp.json():
            print(f"   [DB] Signal {symbol} saved. ID: {resp.json()[0]['id']}")
            return resp.json()[0]['id']
        
        print(f"   [DB FAIL] Status: {resp.status_code} | Body: {resp.text}")
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
        # V900: Broadcast analytics
        redis_engine.publish("live_analytics", data)
        
        # Queue for Supabase
        batch_writer.add_to_batch("analytics_signals", data)
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
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        # V1400: High-Performance Logging
        # 1. Broadcast instantly to UI
        redis_engine.publish("live_logs", data)
        
        # 2. Queue for persistence (No blocking HTTP)
        batch_writer.add_to_batch("error_logs", data)
        
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

def fetch_trade_history(limit=100):
    """V90: Fetches recently closed trades to help the AI learn from results."""
    if not client: return []
    try:
        url = f"{client.base_url}/paper_positions?status=eq.CLOSED&order=closed_at.desc&limit={limit}"
        resp = client.get(url)
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception as e:
        print(f"   !!! History Fetch Error: {e}")
        return []

def upsert_asset_ranking(symbol, score, confidence, trend, reasoning):
    """V90: Syncs the current AI score for an asset (Upsert)."""
    if not client: return
    data = {
        "symbol": symbol,
        "score": float(score),
        "confidence": float(confidence),
        "trend_status": trend,
        "reasoning": reasoning,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    try:
        # Postgrest upsert works by sending ON CONFLICT in the header or just using a specific endpoint
        # For simplicity with the existing client wrapper, we use a custom POST with upsert parameter
        url = f"{client.base_url}/ai_asset_rankings"
        headers = client.headers.copy()
        headers["Prefer"] = "resolution=merge-duplicates"
        client.post(url, json=data, headers=headers)
    except Exception as e:
        print(f"   !!! Ranking Sync Error: {e}")

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
