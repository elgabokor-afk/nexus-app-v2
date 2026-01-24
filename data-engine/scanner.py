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

def calculate_ema(series, period=200):
    return series.ewm(span=period, adjust=False).mean()

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
    
    # 2. Calculate Indicators
    df['RSI'] = calculate_rsi(df['close'], 14)
    df['EMA_200'] = calculate_ema(df['close'], 200)
    df['ATR'] = calculate_atr(df, 14)
    
    # Volume MA for confirmation
    df['Vol_MA'] = df['volume'].rolling(window=20).mean()
    
    latest = df.iloc[-1]
    
    # Metric Extraction
    price = latest['close']
    rsi = latest['RSI']
    ema = latest['EMA_200']
    atr = latest['ATR']
    volume = latest['volume']
    vol_ma = latest['Vol_MA']
    
    # Validation
    if pd.isna(rsi) or pd.isna(ema) or pd.isna(atr):
        return None

    # --- SENIOR LOGIC: CONFIDENCE SCORING (0-100) ---
    score = 50 # Neutral Base
    signal_type = "NEUTRAL"
    
    # 1. RSI Confluence (Max +30)
    if rsi < 30: score += 25       # Deep Oversold
    elif rsi < 45: score += 15     # Dip
    elif rsi > 70: score -= 25     # Deep Overbought
    elif rsi > 55: score -= 15     # Pullback Top
    
    # 2. Trend Filter (Max +10)
    uptrend = price > ema
    if uptrend and rsi < 50: score += 10    # Buying dips in uptrend
    if not uptrend and rsi > 50: score -= 10 # Selling rips in downtrend
    
    # 3. Volume Confirmation (Max +20)
    if volume > (vol_ma * 1.5):
        if uptrend: score += 10
        else: score -= 10
    
    # Determine Signal based on Score
    confidence = 0
    if score >= 75:
        signal_type = "STRONG BUY"
        confidence = score
    elif score >= 65:
        signal_type = "MODERATE BUY"
        confidence = score
    elif score <= 25:
        signal_type = "STRONG SELL"
        confidence = 100 - score # Invert for display confidence
    elif score <= 35:
        signal_type = "MODERATE SELL"
        confidence = 100 - score
        
    if signal_type == "NEUTRAL":
        return None

    # ATR Based Risk Management
    # Buy: SL below price, TP above
    # Sell: SL above price, TP below
    
    stop_loss = 0
    take_profit = 0
    
    if "BUY" in signal_type:
        stop_loss = price - (atr * 1.5)
        take_profit = price + (atr * 2.5)
    else: # SELL
        stop_loss = price + (atr * 1.5)
        take_profit = price - (atr * 2.5)

    return {
        'timestamp': latest['timestamp'],
        'price': price,
        'rsi': round(rsi, 2),
        'signal': signal_type,
        'confidence': int(confidence),
        'stop_loss': round(stop_loss, 4),
        'take_profit': round(take_profit, 4),
        'atr_value': round(atr, 4),
        'volume_ratio': round(volume / vol_ma, 2) if vol_ma > 0 else 1.0
    }

from db import insert_signal, log_error
from telegram_utils import TelegramAlerts

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
                analysis = analyze_market(df)
                
                if analysis:
                    print(f"[{symbol}] Price: {analysis['price']} | RSI: {analysis['rsi']}")
                    if analysis['signal'] != "NEUTRAL":
                        print(f"   >>> SIGNAL: {analysis['signal']} ({analysis['confidence']}%)")
                        # Save to Supabase
                        insert_signal(
                            symbol=symbol,
                            price=float(analysis['price']),
                            rsi=float(analysis['rsi']),
                            signal_type=analysis['signal'],
                            confidence=int(analysis['confidence']),
                            stop_loss=float(analysis['stop_loss']),
                            take_profit=float(analysis['take_profit']),
                            atr_value=float(analysis['atr_value']),
                            volume_ratio=float(analysis['volume_ratio'])
                        )
                        
                        # Broadcast via Telegram
                        tg.send_signal(
                            symbol=symbol,
                            signal_type=analysis['signal'],
                            price=float(analysis['price']),
                            confidence=int(analysis['confidence']),
                            stop_loss=float(analysis['stop_loss']),
                            take_profit=float(analysis['take_profit'])
                        )
                    else:
                        print("   --- No Signal")
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
