import ccxt
import pandas as pd
import time
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()

# 1. Setup Exchange Connection (Kraken - US Friendly)
exchange_config = {
    'enableRateLimit': True,
}

# Use Kraken instead of Binance to avoid 451 Errors in US (Railway)
exchange = ccxt.kraken(exchange_config)
print("Connected to Kraken Exchange")

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
    try:
        # Fetch Level 2 Order Book
        book = exchange.fetch_order_book(symbol, limit=limit)
        return book
    except Exception as e:
        print(f"Error fetching order book for {symbol}: {e}")
        return None

def fetch_data(symbol='BTC/USD', timeframe='1h', limit=100):
    try:
        # Fetch OHLCV (Open, High, Low, Close, Volume)
        bars = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
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
    """Fetch current weight configuration from DB."""
    try:
        res = supabase.table("bot_params").select("*").eq("active", "true").limit(1).execute()
        if res.data:
            p = res.data[0]
            # normalize to ensure they sum to ~1.0 if needed, for now trust DB
            return {
                "rsi": float(p.get('weight_rsi', 0.3)),
                "imbalance": float(p.get('weight_imbalance', 0.3)),
                "trend": float(p.get('weight_trend', 0.2)),
                "macd": float(p.get('weight_macd', 0.2)) 
            }
        return {"rsi": 0.3, "imbalance": 0.3, "trend": 0.2, "macd": 0.2}
    except:
        return {"rsi": 0.3, "imbalance": 0.3, "trend": 0.2, "macd": 0.2}

def analyze_quant_signal(symbol, tech_analysis):
    """
    Combines Technicals (RSI/EMA/MACD) with Quant Data (Order Book)
    using DYNAMIC WEIGHTS from the Optimizer.
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
    
    # 3. APPLY DYNAMIC WEIGHTS
    weights = get_dynamic_weights()
    
    final_score = (
        (rsi_score * weights['rsi']) + 
        (trend_score * weights['trend']) + 
        (imb_score * weights['imbalance']) + 
        (macd_score * weights['macd'])
    )
    
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
    elif ai_prob < 40: ai_boost = -0.20 # -20% Penalty (Safety Net)
    
    final_score = min(1.0, final_score + ai_boost)
    
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
        stop_loss = price - (atr * 1.5)
        take_profit = price + (atr * 2.5)
    else:
        stop_loss = price + (atr * 1.5)
        take_profit = price - (atr * 2.5)
        
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
        'ai_prob': round(ai_prob * 100, 1)
    }

from db import insert_signal, insert_analytics, log_error
from telegram_utils import TelegramAlerts
from cosmos_engine import brain # V8 AI Core

# Initialize Telegram Broadcaster
tg = TelegramAlerts()

# ... (rest of imports)

def main():
    print("/// N E X U S  D A T A  E N G I N E  (v1.0) ///")
    print("Scanning Kraken Spot Markets...")
    print("-" * 50)
    
    # Kraken typically uses USD pairs for high volume
    symbols = [
        'BTC/USD', 'ETH/USD', 'SOL/USD',
        'ADA/USD', 'XRP/USD', 'DOT/USD', 'DOGE/USD',
        'LINK/USD', 'POL/USD', 'LTC/USD', 'BCH/USD',
        'UNI/USD'
    ]
    
    while True:
        try:
            print(f"\n--- Scan at {datetime.now().strftime('%H:%M:%S')} ---")
            for symbol in symbols:
                df = fetch_data(symbol)
                techs = analyze_market(df) # Returns basic tech metrics
                
                if techs:
                    # Upgrade to V4 Analysis
                    quant_signal = analyze_quant_signal(symbol, techs)
                    
                    if quant_signal:
                        print(f"[{symbol}] Price: {quant_signal['price']} | RSI: {quant_signal['rsi']} | Imb: {quant_signal['imbalance']}")
                        print(f"   >>> V4 SIGNAL: {quant_signal['signal']} ({quant_signal['confidence']}%) | Cosmos AI: {quant_signal['ai_prob']}%")
                        
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
                                ai_score=float(quant_signal['ai_prob']/100) # Convert back to 0.0-1.0 for DB
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
