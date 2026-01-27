import time
import json # V405
import requests # V90: Required for Dynamic List
import os
import pandas as pd
import ccxt
from dotenv import load_dotenv
from cosmos_engine import brain
from db import insert_oracle_insight, log_error, insert_signal, insert_analytics, get_active_assets, upsert_asset_ranking, fetch_trade_history

# V415: Robust Path Resolution
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

from binance_engine import live_trader

# V410: Global Config Loading
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
config_path = os.path.join(parent_dir, "config", "conf_global.json")
GLOBAL_CONFIG = {}
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        GLOBAL_CONFIG = json.load(f) or {}

PRIORITY_ASSETS = GLOBAL_CONFIG.get("priority_assets", ["BTC/USDT", "SOL/USDT"])
SYMBOLS = GLOBAL_CONFIG.get("trading_pairs", ["BTC/USDT", "SOL/USDT", "ETH/USDT", "DOGE/USDT"])

# V1500: Dedup Cache
SIGNAL_COOLDOWN = {}

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_ema(series, period=200):
    return series.ewm(span=period, adjust=False).mean()

def calculate_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(period).mean()

def run_oracle_step(symbol='BTC/USDT'):
    """
    V410 Multi-Asset Oracle Step (5m Focus)
    """
    try:
        # 1. FETCH 5m DATA (V410: Shifted from 1m for better signal quality)
        bars = live_trader.fetch_ohlcv(symbol, timeframe='5m', limit=100)
        if not bars or len(bars) < 50:
            print(f"   [ORACLE] Skipping {symbol}: Insufficient data.")
            return

        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # 2. COMPUTE TECHS
        df['RSI'] = calculate_rsi(df['close'])
        df['EMA_200'] = calculate_ema(df['close'])
        df['ATR'] = calculate_atr(df)
        macd, sig, hist = calculate_macd(df['close'])
        
        latest = df.iloc[-1]
        
        features = {
            'price': latest['close'],
            'rsi_value': latest['RSI'],
            'ema_200': latest['EMA_200'],
            'atr_value': latest['ATR'], 
            'histogram': hist.iloc[-1],
            'macd_line': macd.iloc[-1],
            'imbalance_ratio': 0 
        }
        
        # 3. BLM ANALYSIS & RANKING (V90)
        prob = brain.predict_success(features)
        trend = brain.get_trend_status(features)
        reasoning = brain.generate_reasoning(features, prob)
        
        # Calculate Recursive Ranking Score
        # Matches logic in cosmos_engine.rank_assets
        score = prob * 100
        if (trend == "BULLISH" and prob > 0.5): score += 15
        elif (trend == "BEARISH" and prob < 0.5): score += 15
        
        # 4. SYNC RANKING TO SUPABASE (The Neural Link)
        upsert_asset_ranking(symbol, score, prob, trend, reasoning)
        
        # Decide if we should scalp
        signal_type = "STRONG BUY" if prob >= 0.90 and trend == "BULLISH" else \
                      "STRONG SELL" if prob >= 0.90 and trend == "BEARISH" else "NEUTRAL"

        # 5. LOGGING
        print(f"[{time.strftime('%H:%M:%S')}] ORACLE | {symbol.ljust(8)} | {trend.ljust(7)} | Prob: {prob*100:4.1f}% | Rank: {score:.1f}")
        
        # 6. EMIT SCALP SIGNAL
        # V1500: Database Throttling (Spam Protection)
        # Prevents identical signals from flooding the DB.
        # Rule: Cooldown 15m (900s) per symbol unless signal type changes.
        
        signal_key = f"{symbol}_{signal_type}"
        last_signal_time = SIGNAL_COOLDOWN.get(symbol, {}).get("timestamp", 0)
        last_signal_type = SIGNAL_COOLDOWN.get(symbol, {}).get("type", "")
        
        should_emit = False
        
        if signal_type != "NEUTRAL":
            # If type flipped (e.g. BUY -> SELL), emit immediately
            if signal_type != last_signal_type:
                should_emit = True
            # If same type, check 15m cooldown
            elif (time.time() - last_signal_time) > 900:
                should_emit = True
            else:
                # Update cooldown timestamp only (keep alive)
                print(f"      [THROTTLE] Skipping duplicate {symbol} signal (Cooldown active).")

        if should_emit:
            # Update Cache
            SIGNAL_COOLDOWN[symbol] = {"timestamp": time.time(), "type": signal_type}
            
            print(f"      !!! SCALP OPPORTUNITY: {symbol} {signal_type} !!!")
            atr = latest['ATR']
            sl = latest['close'] - (atr * 2.5) if "BUY" in signal_type else latest['close'] + (atr * 2.5)
            tp = latest['close'] + (atr * 2.1) if "BUY" in signal_type else latest['close'] - (atr * 2.1)
            
            sig_id = insert_signal(
                symbol=symbol,
                price=latest['close'],
                rsi=latest['RSI'],
                signal_type=f"{signal_type} (SCALP)",
                confidence=int(prob * 100),
                stop_loss=round(sl, 4),
                take_profit=round(tp, 4),
                atr_value=round(atr, 4)
            )
            
            if sig_id:
                insert_analytics(
                    signal_id=sig_id,
                    ema_200=latest['EMA_200'],
                    rsi_value=latest['RSI'],
                    atr_value=latest['ATR'],
                    imbalance_ratio=0,
                    spread_pct=0,
                    depth_score=0,
                    macd_line=macd.iloc[-1],
                    signal_line=0,
                    histogram=hist.iloc[-1],
                    ai_score=prob
                )

        insert_oracle_insight(
            symbol=symbol,
            timeframe='1m',
            trend=trend,
            prob=prob,
            reasoning=reasoning,
            technical={
                "price": latest['close'],
                "rsi": latest['RSI'],
                "ema_200": latest['EMA_200'],
                "type": "RECURSIVE_RANK_SCAN"
            }
        )

        # V72: Sync Recursive Ranking to Cloud Leaderboard
        upsert_asset_ranking(
            symbol=symbol,
            score=prob * 100, # Use prob as base score for ranking
            confidence=prob,
            trend=trend,
            reasoning=reasoning
        )

        # V1400: Redis Broadcast (Low Latency)
        # Decouples the frontend from Supabase Realtime
        from redis_engine import redis_engine
        redis_engine.publish("ai_rankings", {
            "symbol": symbol,
            "score": prob * 100,
            "confidence": prob,
            "trend_status": trend,
            "reasoning": reasoning,
            "updated_at": time.time()
        })
        
    except Exception as e:
        print(f"!!! Oracle Error ({symbol}): {e}")
        log_error(f"ORACLE_{symbol}", e, "ERROR")

import requests # V90: Required for Dynamic List

# ... (Previous Imports)
# Just creating a local helper to avoid circular import issues with scanner.py
def get_top_vol_oracle(limit=20):
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        res = requests.get(url, timeout=10)
        data = res.json()
        
        # Filter USDT
        usdt_pairs = [
            t for t in data 
            if t['symbol'].endswith('USDT') 
            and 'UP' not in t['symbol'] 
            and 'DOWN' not in t['symbol']
        ]
        
        # Sort by Quote Volume
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
        
        top_symbols = []
        for p in sorted_pairs[:limit]:
            sym = p['symbol']
            formatted = f"{sym[:-4]}/{sym[-4:]}"
            top_symbols.append(formatted)
            
        print(f">>> [ORACLE V90] Dynamic Top {limit} Asset List Updated: {top_symbols}")
        return top_symbols
    except Exception as e:
        print(f"!!! [ORACLE V90] Failed to fetch top assets: {e}")
        return []

if __name__ == "__main__":
    print("--- COSMOS RECURSIVE ORACLE V90 STARTED ---")
    print("Broadcasting Live Rankings & AI Insights for Top 20 Portfolio.")
    
    # V90: Initial Recursive Sync
    print(">>> Performing Initial Recursive Analysis...")
    history = fetch_trade_history(limit=100)
    brain.update_asset_bias(history)
    
    last_recursive_sync = time.time()
    last_asset_update = 0
    dynamic_assets = []
    
    while True:
        # V90: Refresh recursive logic every hour
        if time.time() - last_recursive_sync > 3600:
            print(">>> Hourly Recursive Sync: Analyzing latest results...")
            history = fetch_trade_history(limit=100)
            brain.update_asset_bias(history)
            last_recursive_sync = time.time()

        # V24: Dynamic Asset List Update (Every 30m)
        if time.time() - last_asset_update > 1800:
            print(">>> [ORACLE V90] Refreshing Dynamic Top-20 Priority List...")
            dynamic_assets = get_top_vol_oracle(limit=20)
            last_asset_update = time.time()

        # V410: Priority Pulse (BTC/SOL first)
        active_assets = get_active_assets()
        
        # Merge: Priority (Config) + Active (DB) + Dynamic (Binance) + Standard (Config)
        all_unique_assets = list(set(active_assets + PRIORITY_ASSETS + dynamic_assets + SYMBOLS))
        
        # Ensure Priority Assets are scanned FIRST
        target_assets = PRIORITY_ASSETS + [a for a in dynamic_assets if a not in PRIORITY_ASSETS] + [a for a in all_unique_assets if a not in PRIORITY_ASSETS and a not in dynamic_assets]
        
        print(f"\n>>> Starting Recursive Pulse for {len(target_assets)} assets...")
        print(f"    [PRIORITY]: {PRIORITY_ASSETS}")
        print(f"    [DYNAMIC]:  {len(dynamic_assets)} found")
        print(f"    [STANDARD]: {len(SYMBOLS)} additional")
        
        for symbol in target_assets:
            run_oracle_step(symbol)
            time.sleep(2) # Small delay to avoid rate limits
            
        print(f">>> Pulse Complete. Sleeping 30s...")
        time.sleep(30) 
 

