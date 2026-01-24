import os
import time
import pandas as pd
import numpy as np
import ccxt
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from dotenv import load_dotenv

# Path Fixing for imports
load_dotenv(dotenv_path="../.env.local")

# KRAKEN CONFIG
exchange = ccxt.kraken({
    'enableRateLimit': True,
})

MODEL_PATH = "cosmos_model.joblib"
FEATURE_COLS = ['rsi_value', 'imbalance_ratio', 'spread_pct', 'atr_value', 'macd_line', 'histogram']

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
    return macd_line, histogram

def calculate_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(14).mean()

def fetch_historical_data(symbol='BTC/USD', timeframe='15m', limit=2000):
    print(f"   >>> Fetching {limit} historical candles for {symbol} ({timeframe})...")
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df

def bootstrap_brain():
    """
    V70 Local Bootstrapper:
    1. Downloads history
    2. Labels successes (Price +1.5% before -1%)
    3. Trains Local Brain
    """
    print("--- COSMOS AI LOCAL BOOTSTRAPPER (V70) ---")
    
    # 1. Fetch Data
    df = fetch_historical_data()
    
    # 2. Compute Features
    print("   >>> Computing technical indicators...")
    df['rsi_value'] = calculate_rsi(df['close'])
    df['atr_value'] = calculate_atr(df)
    macd_line, histogram = calculate_macd(df['close'])
    df['macd_line'] = macd_line
    df['histogram'] = histogram
    df['imbalance_ratio'] = 0 # Synthetic placeholder
    df['spread_pct'] = 0.0002 # Average Kraken spread
    
    # 3. AUTO-LABELLING (Look Ahead)
    print("   >>> Labelling winning patterns (15m window)...")
    df['target'] = 0
    window = 20 # Look 20 bars ahead
    
    for i in range(len(df) - window):
        current_price = df.iloc[i]['close']
        future_prices = df.iloc[i+1 : i+window]['high']
        future_lows = df.iloc[i+1 : i+window]['low']
        
        # Win Condition: Price goes up 1.5% before dropping 1%
        target_profit = current_price * 1.015
        stop_loss = current_price * 0.99
        
        hit_tp = (future_prices >= target_profit).any()
        hit_sl = (future_lows <= stop_loss).any()
        
        if hit_tp and not (hit_sl and future_lows[future_lows <= stop_loss].index[0] < future_prices[future_prices >= target_profit].index[0]):
            df.at[i, 'target'] = 1

    # 4. TRAIN MODEL
    X = df[FEATURE_COLS].dropna()
    y = df.loc[X.index, 'target']
    
    print(f"   >>> Training on {len(X)} samples... (Wins: {y.sum()})")
    
    imputer = SimpleImputer(strategy='mean')
    X_imputed = imputer.fit_transform(X)
    
    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_imputed, y)
    
    # 5. SAVE
    joblib.dump({'model': model, 'imputer': imputer}, MODEL_PATH)
    
    accuracy = model.score(X_imputed, y)
    print(f"--- BOOTSTRAP COMPLETE ---")
    print(f"Local AI Brain created with {accuracy:.2%} historical accuracy.")
    print(f"Knowledge saved to: {MODEL_PATH}")

if __name__ == "__main__":
    bootstrap_brain()
