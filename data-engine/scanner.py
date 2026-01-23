import ccxt
import pandas as pd
import time
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()

# 1. Setup Binance Connection
exchange_config = {
    'enableRateLimit': True,
}

# Check for Proxy
proxy_url = os.getenv('PROXY_URL')
if proxy_url:
    print(f"Using Proxy: {proxy_url}")
    exchange_config['proxies'] = {
        'http': proxy_url,
        'https': proxy_url,
    }

exchange = ccxt.binance(exchange_config)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(series, period=200):
    return series.ewm(span=period, adjust=False).mean()

def fetch_data(symbol='BTC/USDT', timeframe='1h', limit=100):
    try:
        # Fetch OHLCV (Open, High, Low, Close, Volume)
        bars = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def analyze_market(df):
    if df.empty:
        return None
    
    # 2. Calculate Indicators (Manual Pandas)
    # RSI 14
    df['RSI'] = calculate_rsi(df['close'], 14)
    # EMA 200
    df['EMA_200'] = calculate_ema(df['close'], 200)
    
    # Get latest values
    latest = df.iloc[-1]
    
    signal = "NEUTRAL"
    confidence = 0
    
    # Simple Logic: RSI Oversold + Above EMA (Trend Pullback)
    rsi_val = latest['RSI']
    close_val = latest['close']
    ema_val = latest['EMA_200']
    
    # Handle NaN at start of series
    if pd.isna(rsi_val) or pd.isna(ema_val):
        return None

    if rsi_val < 30 and close_val > ema_val:
        signal = "STRONG BUY (Oversold in Uptrend)"
        confidence = 90
    elif rsi_val > 70 and close_val < ema_val:
        signal = "STRONG SELL (Overbought in Downtrend)"
        confidence = 85
    
    return {
        'timestamp': latest['timestamp'],
        'price': close_val,
        'rsi': round(rsi_val, 2),
        'signal': signal,
        'confidence': confidence
    }

from db import insert_signal

# ... (rest of imports)

def main():
    print("/// N E X U S  D A T A  E N G I N E  (v1.0) ///")
    print("Scanning Binance Spot Markets...")
    print("-" * 50)
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
    
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
                    confidence=int(analysis['confidence'])
                )
            else:
                print("   --- No Signal")
        time.sleep(0.5) # Rate limit friendly

if __name__ == "__main__":
    main()
