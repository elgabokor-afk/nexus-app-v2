import ccxt
import pandas as pd
import requests
import time
import json # V405
from datetime import datetime

import os
from dotenv import load_dotenv

# Load env from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

# V301: GLOBAL ASSET BLACKLIST (V412: Added DOGE)
ASSET_BLACKLIST = ['PEPE', 'PEPE/USDT', 'PEPE/USD', 'DOGE', 'DOGE/USDT']

# V310: Import Binance Engine for unified data/execution
from binance_engine import live_trader

# V410: Global Config Loading
config_path = os.path.join(parent_dir, "config", "conf_global.json")
GLOBAL_CONFIG = {}
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        GLOBAL_CONFIG = json.load(f) or {}

PRIORITY_ASSETS = GLOBAL_CONFIG.get("priority_assets", ["BTC/USDT", "SOL/USDT"])
ANALYSIS_TIMEFRAMES = GLOBAL_CONFIG.get("analysis_timeframes", ["5m", "15m"])
SYMBOLS = GLOBAL_CONFIG.get("trading_pairs", ["BTC/USDT", "SOL/USDT", "ETH/USDT"])

print("--- BINANCE DATA ENGINE ACTIVE (V310 Migration) ---")

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

def fetch_order_book(symbol='BTC/USD', limit=50):
    """V310: Use Binance for Order Book."""
    try:
        # Map symbol if needed, but Binance/CCXT handles /USDT well
        return live_trader.fetch_order_book(symbol, limit=limit)
    except Exception as e:
        print(f"Error fetching order book for {symbol}: {e}")
        return None

def fetch_data(symbol='BTC/USD', timeframe='1h', limit=100):
    """V310: Use Binance for OHLCV."""
    try:
        bars = live_trader.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not bars: return pd.DataFrame()
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def calculate_imbalance(book):
    """
    Calculates Order Book Imbalance.
    Formula: (Bid_Vol - Ask_Vol) / (Bid_Vol + Ask_Vol)
    Returns: -1.0 (Bearish) to 1.0 (Bullish)
    """
    if not book: return 0
    
    bids = book['bids']
    asks = book['asks']
    
    bid_vol = sum([b[1] for b in bids])
    ask_vol = sum([a[1] for a in asks])
    
    total_vol = bid_vol + ask_vol
    if total_vol == 0: return 0
    
    imbalance = (bid_vol - ask_vol) / total_vol
    return imbalance

def calculate_atr(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close'].shift(1)
    
    tr1 = high - low
    tr2 = (high - close).abs()
    tr3 = (low - close).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr

def analyze_market(df):
    if df.empty or len(df) < 50:
        return None
    
    # Calculate Indicators
    df['RSI'] = calculate_rsi(df['close'], 14)
    df['EMA_200'] = calculate_ema(df['close'], 200)
    df['ATR'] = calculate_atr(df, 14)
    
    # MACD
    macd, sig, hist = calculate_macd(df['close'])
    df['MACD'] = macd
    df['Signal_Line'] = sig
    df['Histogram'] = hist
    
    # Volume MA
    df['Vol_MA'] = df['volume'].rolling(window=20).mean()
    
    latest = df.iloc[-1]
    
    # Validation
    if pd.isna(latest['RSI']) or pd.isna(latest['EMA_200']):
        return None

    return {
        'timestamp': latest['timestamp'],
        'symbol': df.attrs.get('symbol', 'BTC/USD'), # Fallback
        'price': latest['close'],
        'rsi': latest['RSI'],
        'ema_200': latest['EMA_200'],
        'atr': latest['ATR'],
        'volume': latest['volume'],
        'vol_ma': latest['Vol_MA'],
        'macd': latest['MACD'],
        'signal_line': latest['Signal_Line'],
        'histogram': latest['Histogram']
    }

from supabase import create_client, Client
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_dynamic_weights():
    """Fetch current configuration from DB (Weights + Risk)."""
    try:
        res = supabase.table("bot_params").select("*").eq("active", "true").limit(1).execute()
        if res.data:
            p = res.data[0]
            # normalize to ensure they sum to ~1.0 if needed, for now trust DB
            return {
                "rsi": float(p.get('weight_rsi', 0.3)),
                "imbalance": float(p.get('weight_imbalance', 0.3)),
                "trend": float(p.get('weight_trend', 0.2)),
                "macd": float(p.get('weight_macd', 0.2)),
                "max_open_positions": int(p.get('max_open_positions', 3)),
                "cooldown_minutes": int(p.get('cooldown_minutes', 15))
            }
        return {"rsi": 0.3, "imbalance": 0.3, "trend": 0.2, "macd": 0.2, "max_open_positions": 3, "cooldown_minutes": 15}
    except:
        return {"rsi": 0.3, "imbalance": 0.3, "trend": 0.2, "macd": 0.2, "max_open_positions": 3, "cooldown_minutes": 15}

def fetch_fear_greed():
    """
    Fetches the Fear & Greed Index from Alternative.me.
    Returns: int (0-100), default 50 (Neutral)
    """
    try:
        # 1 day cache could be implemented, but the API is free for limited use.
        # We will call this once per scan cycle (approx every 2 mins), which is fine.
        response = requests.get("https://api.alternative.me/fng/")
        if response.status_code == 200:
            data = response.json()
            # Structure: {'data': [{'value': '25', ...}]}
            idx = int(data['data'][0]['value'])
            return idx
    except Exception as e:
        print(f"Warning: Could not fetch Fear & Greed Index: {e}")
    return 50 # Default Neutral

# V415: Triple Confluence Helper Functions

def check_rsi_divergence(df, lookback=10):
    """
    Detects simple RSI Divergence.
    Bullish: Price Lower Low, RSI Higher Low
    Bearish: Price Higher High, RSI Lower High
    """
    if len(df) < lookback: return "NONE"
    
    price = df['close'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    
    # Simple logic: Compare current vs lowest/highest in lookback
    window = df.iloc[-lookback:-1]
    
    if rsi < 35: # Potential Bullish Div
        min_price_idx = window['close'].idxmin()
        min_price = window['close'][min_price_idx]
        min_rsi = window['RSI'][min_price_idx]
        
        if price < min_price and rsi > min_rsi:
            return "BULLISH"
            
    if rsi > 65: # Potential Bearish Div
        max_price_idx = window['close'].idxmax()
        max_price = window['close'][max_price_idx]
        max_rsi = window['RSI'][max_price_idx]
        
        if price > max_price and rsi < max_rsi:
            return "BEARISH"
            
    return "NONE"

def analyze_volume_pressure(df):
    """
    Calculates Volume Pressure Ratio.
    Formula: Current Volume / 20-period Volume MA
    Threshold: > 1.2 is significant.
    """
    vol = df['volume'].iloc[-1]
    ma = df['Vol_MA'].iloc[-1]
    if ma == 0: return 1.0
    return vol / ma

def check_market_structure(df, lookback=20):
    """
    Approximation of MSB (Market Structure Break).
    Bullish: Close > Highest High of last X periods (Breakout)
    Bearish: Close < Lowest Low of last X periods (Breakdown)
    """
    current_close = df['close'].iloc[-1]
    window = df.iloc[-lookback:-1]
    
    highest = window['high'].max()
    lowest = window['low'].min()
    
    if current_close > highest:
        return "BULLISH"
    elif current_close < lowest:
        return "BEARISH"
    
    return "NEUTRAL"

def check_news_blackout():
    """
    Manual News Filter (Placeholder).
    Returns TRUE if in blackout window.
    """
    # TODO: Integrate valid news API. For now, we trust the manual schedule.
    # Logic: Avoid 8:30am EST and 2:00pm EST ? 
    # Let's keep it simple: No blackout unless manually added here.
    return False

def analyze_quant_signal(symbol, tech_analysis, sentiment_score=50, df_confluence=None, df_htf=None):
    """
    Combines Technicals (RSI/EMA/MACD) with Quant Data (Order Book)
    using DYNAMIC WEIGHTS from the Optimizer.
    V14: Added df_htf for H4 S/R checks.
    """
    if not tech_analysis: return None
    
    price = tech_analysis['price']
    rsi = tech_analysis['rsi']
    
    # 1. Fetch Liquidity Data
    book = fetch_order_book(symbol)
    imbalance = calculate_imbalance(book) # -1 to 1
    
    # Spread Calculation
    best_bid = book['bids'][0][0] if book['bids'] else price
    best_ask = book['asks'][0][0] if book['asks'] else price
    spread_pct = ((best_ask - best_bid) / price) * 100
    
    # 2. SCORING COMPONENTS (0.0 to 1.0)
    
    # RSI Score (Mean Reversion preference)
    # Low RSI -> Bullish (1.0), High RSI -> Bearish (0.0)
    rsi_score = 0.5
    if rsi < 30: rsi_score = 1.0
    elif rsi > 70: rsi_score = 0.0
    else: rsi_score = 1.0 - ((rsi - 30) / 40)
    
    # Trend Score (EMA 200)
    trend_score = 1.0 if price > tech_analysis['ema_200'] else 0.0
    
    # Imbalance Score (-1 to 1 -> 0 to 1)
    # +1 Imbalance (All Bids) -> Bullish (1.0)
    imb_score = (imbalance + 1) / 2
    
    # MACD Score (Momentum)
    # Histogram > 0 -> Bullish
    hist = tech_analysis['histogram']
    macd_score = 0.5
    if hist > 0: macd_score = 0.8
    if hist < 0: macd_score = 0.2
    if hist > 0 and tech_analysis['macd'] > 0: macd_score = 1.0
    
    # V415: TRIPLE CONFLUENCE CHECK
    # 1. Structure
    structure = "NEUTRAL"
    if df_confluence is not None:
        structure = check_market_structure(df_confluence)
    
    # 2. RSI Divergence
    divergence = "NONE"
    if df_confluence is not None:
        divergence = check_rsi_divergence(df_confluence)
        
    # 3. Volume Pressure
    vol_pressure = 1.0
    if df_confluence is not None:
        vol_pressure = analyze_volume_pressure(df_confluence)
        
    # LOGIC UPDATE: High Probability Filters
    
    # V1400: Volume Filter (Strict)
    # Signal discarded if current volume < 20-period MA (vol_pressure < 1.0)
    # We allow a small tolerance (0.95) to avoid over-filtering slightly quiet breakouts
    if vol_pressure < 0.95:
        return None 
        
    # V1400: Weight Penalty for Weak Volume (even if pass)
    if vol_pressure < 1.2:
        # Weak Volume -> Penalty
        macd_score *= 0.5
        imb_score *= 0.5
        
    # V1400: H4 Structure / Resistance Filter
    # If price is approaching H4 Resistance (High of last 20 candles), dampen Bullish confidence
    if df_htf is not None:
        htf_lookback = df_htf.iloc[-20:-1]
        htf_high = htf_lookback['high'].max()
        htf_low = htf_lookback['low'].min()
        
        # Proximity defined as within 1% of key level
        dist_to_res = (htf_high - price) / price
        dist_to_sup = (price - htf_low) / price
        
        # If Bullish Signal but close to H4 Resistance (< 0.5% away)
        if dist_to_res < 0.005 and rsi_score > 0.5:
             # Serious Penalty
             rsi_score *= 0.5
             trend_score *= 0.5
             print(f"   [FILTER] {symbol} dampened by H4 Resistance proximity.")
             
        # If Bearish Signal but close to H4 Support (< 0.5% away)
        if dist_to_sup < 0.005 and rsi_score < 0.5:
             rsi_score = 1.0 - (1.0 - rsi_score) * 0.5 # Dampen bearishness
             trend_score *= 0.5
             print(f"   [FILTER] {symbol} dampened by H4 Support proximity.")
        
    # 3. APPLY DYNAMIC WEIGHTS
    weights = get_dynamic_weights()
    
    final_score = (
        (rsi_score * weights['rsi']) + 
        (trend_score * weights['trend']) + 
        (imb_score * weights['imbalance']) + 
        (macd_score * weights['macd'])
    )
    
    # TRIPLE CONFLUENCE BONUSES
    if structure == "BULLISH" and rsi_score > 0.5: final_score += 0.1
    if structure == "BEARISH" and rsi_score < 0.5: final_score += 0.1
    
    if divergence == "BULLISH" and rsi_score > 0.5: final_score += 0.15 # Strong signal
    if divergence == "BEARISH" and rsi_score < 0.5: final_score += 0.15 # Strong signal
    
    if vol_pressure > 2.0: final_score += 0.1 # Whale activity
    elif vol_pressure > 1.5: final_score += 0.05
    
    # Check News Blackout
    if check_news_blackout():
        print(f"   [NEWS FILTER] Signal suppressed during blackout.")
        return None
    
    # V8 COSMOS AI PREDICTION
    # Ask the Brain: "What are the odds?"
    features = {
        'rsi_value': rsi,
        'imbalance_ratio': imbalance,
        'spread_pct': spread_pct,
        'atr_value': tech_analysis['atr'],
        'macd_line': tech_analysis['macd'],
        'histogram': tech_analysis['histogram']
    }
    ai_prob = brain.predict_success(features) # Returns 0.0 to 1.0 (e.g., 0.65)
    
    # Hybrid Score Adjustment
    # If AI is confident (>60%), boost score. If doubtful (<40%), penalize.
    ai_boost = 0
    if ai_prob > 0.60: ai_boost = 0.10 # +10% Confidence
    elif ai_prob < 0.40: ai_boost = -0.20 # -20% Penalty (Safety Net)
    
    # V9 SENTIMENT ANALYSIS (Fear & Greed)
    # Contrarian Logic: Buy when fearful, Sell when greedy
    sentiment_boost = 0
    if sentiment_score <= 25: sentiment_boost = 0.15 # Extreme Fear -> Buy Opportunity
    elif sentiment_score <= 40: sentiment_boost = 0.08 # Fear
    elif sentiment_score >= 75: sentiment_boost = -0.15 # Extreme Greed -> Sell Risk
    elif sentiment_score >= 60: sentiment_boost = -0.08 # Greed
    
    final_score = final_score + ai_boost + sentiment_boost
    final_score = max(0.0, min(1.0, final_score)) # Clamp
    
    final_confidence = int(final_score * 100)
    
    # DETERMINE SIGNAL
    signal_type = "NEUTRAL"
    if final_confidence >= 65: signal_type = "STRONG BUY"
    elif final_confidence >= 50: signal_type = "MODERATE BUY"
    elif final_confidence <= 35: signal_type = "STRONG SELL"
    elif final_confidence <= 50: signal_type = "MODERATE SELL"
    
    if signal_type == "NEUTRAL": return None
    
    # ATR Risk Logic
    atr = tech_analysis['atr']
    if "BUY" in signal_type:
        stop_loss = price - (atr * 1.5) # User requested 1.5x
        take_profit = price + (atr * 3.0) # User requested 3.0x (1:2 Ratio)
    else:
        stop_loss = price + (atr * 1.5)
        take_profit = price - (atr * 3.0)
        
    return {
        'signal': signal_type,
        'confidence': final_confidence,
        'price': price,
        'rsi': rsi,
        'stop_loss': round(stop_loss, 4),
        'take_profit': round(take_profit, 4),
        'atr_value': round(atr, 4),
        'ema_200': round(tech_analysis['ema_200'], 4),
        'imbalance': round(imbalance, 4),
        'spread_pct': round(spread_pct, 4),
        'depth_score': int(weights['imbalance'] * 100), # Proxy showing how much we trust depth
        'macd': round(tech_analysis['macd'], 4),
        'signal_line': round(tech_analysis['signal_line'], 4),
        'histogram': round(tech_analysis['histogram'], 4),
        'ai_prob': round(ai_prob * 100, 1),
        'sentiment': sentiment_score,
        'volume_ratio': round(vol_pressure, 2),
        'depth_score': int(vol_pressure * 100) # Keep for legacy support if any
    }

from db import insert_signal, insert_analytics, log_error, get_active_position_count, get_last_trade_time
from telegram_utils import TelegramAlerts
from cosmos_engine import brain # V8 AI Core

# Initialize Telegram Broadcaster
tg = TelegramAlerts()

def get_top_vol_pairs(limit=15):
    """
    Fetches Top 15 USDT pairs by 24h Quote Volume from Binance.
    """
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        res = requests.get(url, timeout=10)
        data = res.json()
        
        # V3001: Defensive Check - Handle Error Responses (Dict instead of List)
        if not isinstance(data, list):
            print(f"   [DYNAMIC] Binance API Warning: Expected List, got {type(data)}. Payload: {str(data)[:100]}")
            return []

        # Filter USDT, exclude leveraged tokens
        usdt_pairs = [
            t for t in data 
            if isinstance(t, dict) and 'symbol' in t and t['symbol'].endswith('USDT') 
            and 'UP' not in t['symbol'] 
            and 'DOWN' not in t['symbol']
        ]
        
        # Sort by Volume Desc
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
        
        # Extract symbols, format to CCXT standard (BTC/USDT)
        top_symbols = []
        for p in sorted_pairs[:limit]:
            sym = p['symbol']
            # Convert BTCUSDT -> BTC/USDT
            formatted = f"{sym[:-4]}/{sym[-4:]}"
            top_symbols.append(formatted)
            
        print(f"   [DYNAMIC] Top {limit} Vol Assets: {top_symbols}")
        return top_symbols
    except Exception as e:
        print(f"   [DYNAMIC] Failed to fetch top stats: {e}")
        return []

def main():
    print("/// N E X U S  D A T A  E N G I N E  (v1.0) ///")
    print(f"Priority Focus: {PRIORITY_ASSETS}")
    print("-" * 50)
    
    # V10.0: Initial AI Training (Startup)
    print("--- [SVC] Initializing Cosmos AI Brain ---")
    brain.train()
    last_train_time = datetime.now()
    train_interval_hours = 6
    
    # V24: Auto-Update Top Assets
    last_asset_update = 0
    
    while True:
        try:
            # Check for Re-Training
            now = datetime.now()
            elapsed = (now - last_train_time).total_seconds() / 3600
            if elapsed >= train_interval_hours:
                print(f"--- [SVC] Cosmos Brain: Scheduled Retraining ({train_interval_hours}h elapsed) ---")
                brain.train()
                last_train_time = now
            
            # V24: Dynamic Asset List Update (Every 1 Hour)
            # We merge PRIORITY_ASSETS (Fixed) + TOP_VOL_ASSETS (Dynamic)
            if time.time() - last_asset_update > 3600:
                print("--- [DYNAMIC] Refreshing Top Volume Assets ---")
                dynamic_pairs = get_top_vol_pairs(limit=15)
                # Merge Unique: Priority + Dynamic + Standard Symbols (Fallback)
                current_scan_list = list(set(PRIORITY_ASSETS + dynamic_pairs + SYMBOLS))
                last_asset_update = time.time()
                print(f"   [SCAN LIST] Total: {len(current_scan_list)} Pairs (Dynamic: {len(dynamic_pairs)})")
            
            # 1. Fetch Global Data (Sentiment)
            fng_index = fetch_fear_greed()
            
            # V12.0: RISK GUARD CHECK
            params = get_dynamic_weights()
            active_positions = get_active_position_count()
            
            # Max Positions Limit
            if active_positions >= params['max_open_positions']:
                print(f"\n[RISK GUARD] Max Positions Reached ({active_positions}/{params['max_open_positions']}). Scanning Paused.")
                time.sleep(30)
                continue

            # Cooldown Check
            last_trade_ts_str = get_last_trade_time()
            if last_trade_ts_str:
                try:
                    last_trade = datetime.fromisoformat(last_trade_ts_str.replace('Z', '+00:00'))
                    if last_trade.tzinfo is None:
                        last_trade = last_trade.replace(tzinfo=datetime.now().astimezone().tzinfo)
                    
                    current_localized = datetime.now(last_trade.tzinfo)
                    mins_since = (current_localized - last_trade).total_seconds() / 60
                    
                    if mins_since < params['cooldown_minutes']:
                         print(f"\n[RISK GUARD] Cooling Down... {int(mins_since)}/{params['cooldown_minutes']} mins. Scanning Paused.")
                         time.sleep(30)
                         continue
                except Exception as e:
                    print(f"Date Parse Warning: {e}")

            print(f"\n--- Scan at {now.strftime('%H:%M:%S')} | Fear & Greed: {fng_index} | Open: {active_positions} ---")
            
            # Use current_scan_list for the loop
            # Fallback if dynamic list failed initially
            if 'current_scan_list' not in locals() or not current_scan_list:
                current_scan_list = PRIORITY_ASSETS + [s for s in SYMBOLS if s not in PRIORITY_ASSETS]
                
            print(f"   [PORTFOLIO FLOW] Scanning {len(current_scan_list)} Assets...")
            
            for symbol in current_scan_list:
                if any(b in symbol.upper() for b in ASSET_BLACKLIST):
                    continue
                
                # V410: Multi-Timeframe Confluence (5m & 15m)
                # We analyze the faster timeframe (5m) for entries, confirmed by 15m trend.
                df_5m = fetch_data(symbol, timeframe='5m', limit=100)
                df_15m = fetch_data(symbol, timeframe='15m', limit=100)
                
                techs_5m = analyze_market(df_5m)
                techs_15m = analyze_market(df_15m)
                
                if techs_5m and techs_15m:
                    # Logic: 5m signal MUST align with 15m EMA_200 trend
                    ma_15m = techs_15m['ema_200']
                    p_5m = techs_5m['price']
                    trend_15m = "BULLISH" if p_5m > ma_15m else "BEARISH"
                    
                    # Upgrade to V4 Analysis with Confluence (Pass the DF for history checks)
                    quant_signal = analyze_quant_signal(symbol, techs_5m, sentiment_score=fng_index, df_confluence=df_5m)
                    
                    if quant_signal:
                        # V410: STRENGTHEN FILTER - Confluence check
                        # If 5m signal is BUY, 15m MUST be BULLISH
                        if "BUY" in quant_signal['signal'] and trend_15m != "BULLISH":
                            print(f"   [V410 FILTER] {symbol} 5m BUY rejected: 15m Trend is BEARISH.")
                            quant_signal = None
                        elif "SELL" in quant_signal['signal'] and trend_15m != "BEARISH":
                            print(f"   [V410 FILTER] {symbol} 5m SELL rejected: 15m Trend is BULLISH.")
                            quant_signal = None

                    if quant_signal:
                        print(f"[{symbol}] Price: {quant_signal['price']} | RSI: {quant_signal['rsi']} | Imb: {quant_signal['imbalance']}")
                        print(f"   >>> V410 CONFLUENCE SIGNAL: {quant_signal['signal']} ({quant_signal['confidence']}%) | Trend(15m): {trend_15m}")
                        
                        # ... (DB Insert Logic) ...
                        # 1. Insert Base Signal
                        sig_id = insert_signal(
                            symbol=symbol,
                            price=float(quant_signal['price']),
                            rsi=float(quant_signal['rsi']),
                            signal_type=quant_signal['signal'],
                            confidence=int(quant_signal['confidence']),
                            stop_loss=float(quant_signal['stop_loss']),
                            take_profit=float(quant_signal['take_profit']),
                            atr_value=float(quant_signal['atr_value']),
                            volume_ratio=float(quant_signal['depth_score']/100) # Approx
                        )
                        
                        # 2. Insert Quant Analytics
                        if sig_id:
                            insert_analytics(
                                signal_id=sig_id,
                                ema_200=quant_signal['ema_200'],
                                rsi_value=quant_signal['rsi'],
                                atr_value=quant_signal['atr_value'],
                                imbalance_ratio=quant_signal['imbalance'],
                                spread_pct=quant_signal['spread_pct'],
                                depth_score=quant_signal['depth_score'],
                                macd_line=quant_signal['macd'],
                                signal_line=quant_signal['signal_line'],
                                histogram=quant_signal['histogram'],
                                ai_score=float(quant_signal['ai_prob']/100), # Convert back to 0.0-1.0 for DB
                                sentiment_score=quant_signal['sentiment']
                            )
                        
                        # Broadcast via Telegram
                        tg.send_signal(
                            symbol=symbol,
                            signal_type=quant_signal['signal'],
                            price=float(quant_signal['price']),
                            confidence=int(quant_signal['confidence']),
                            stop_loss=float(quant_signal['stop_loss']),
                            take_profit=float(quant_signal['take_profit'])
                        )
                    else:
                        # DEBUG: Why no signal?
                        # Re-calculate score to show user why
                        # (Ideally analyze_quant_signal returns the score even if neutral, but it returns None currently)
                        # Let's verify by calling a modified version or just trusting the logic is strict.
                        # For now, let's print a "Scanning..." message with basic metrics to prove it's alive.
                        print(f"   --- No Signal ({symbol}) -> RSI: {techs['rsi']:.1f}")
                time.sleep(1) # Rate limit friendly per symbol

            print("Waiting 60s for next scan...")
            time.sleep(60)
            
        except Exception as e:
            error_msg = f"Scanner Main Loop Error: {e}"
            print(f"!!! CRITICAL ERROR: {error_msg}")
            log_error("scanner", error_msg, error_level="CRITICAL")
            tg.send_error(error_msg)
            time.sleep(60)

if __name__ == "__main__":
    main()
