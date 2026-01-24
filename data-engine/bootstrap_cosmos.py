import os
import time
import pandas as pd
import numpy as np
import ccxt
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from dotenv import load_dotenv
from db import sync_model_metadata

# Path Fixing for imports
load_dotenv(dotenv_path="../.env.local")

# V310: BINANCE CONFIG (Replaces Kraken)
exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_SECRET'),
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

def fetch_historical_data(symbol='BTC/USDT', timeframe='15m', limit=2000):
    """V310: Fetch historical data from Binance."""
    print(f"   >>> Fetching {limit} historical candles for {symbol} ({timeframe})...")
    # Ensure symbol is Binance compatible (e.g. BTC/USDT)
    binance_symbol = symbol.replace('/USD', '/USDT')
    bars = exchange.fetch_ohlcv(binance_symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df

def bootstrap_brain():
    """
    V70/V80 Local Bootstrapper:
    1. Downloads history for ALL active assets
    2. Labels successes
    3. Trains Local Brain on Multi-Asset data
    """
    print("--- COSMOS AI MULTI-ASSET BOOTSTRAPPER (V80) ---")
    
    from db import get_active_assets
    target_assets = get_active_assets()
    
    all_dfs = []
    
    for symbol in target_assets:
        # 1. Fetch Data
        df = fetch_historical_data(symbol)
        if df.empty: continue
        
        # 2. Compute Features
        print(f"   >>> Computing indicators for {symbol}...")
        df['symbol'] = symbol
        df['rsi_value'] = calculate_rsi(df['close'])
        df['atr_value'] = calculate_atr(df)
        macd_line, histogram = calculate_macd(df['close'])
        df['macd_line'] = macd_line
        df['histogram'] = histogram
        df['imbalance_ratio'] = 0 
        df['spread_pct'] = 0.0002
        
        # 3. AUTO-LABELLING (Look Ahead)
        df['target'] = 0
        window = 20 
        
        for i in range(len(df) - window):
            current_price = df.iloc[i]['close']
            future_prices = df.iloc[i+1 : i+window]['high']
            future_lows = df.iloc[i+1 : i+window]['low']
            
            target_profit = current_price * 1.015
            stop_loss = current_price * 0.99
            
            hit_tp = (future_prices >= target_profit).any()
            hit_sl = (future_lows <= stop_loss).any()
            
            if hit_tp:
                # Basic check: did we hit TP before SL?
                tp_idx = future_prices[future_prices >= target_profit].index[0]
                sl_idx = future_lows[future_lows <= stop_loss].index[0] if hit_sl else 999999
                
                if tp_idx < sl_idx:
                    df.at[i, 'target'] = 1

        all_dfs.append(df)
        time.sleep(1) # Delay for rate limits
    
    if not all_dfs:
        print("!!! Error: No data collected. Bootstrap failed.")
        return

    combined_df = pd.concat(all_dfs)
    
    # 4. TRAIN MODEL
    X = combined_df[FEATURE_COLS].dropna()
    y = combined_df.loc[X.index, 'target']
    
    print(f"   >>> Combined Training on {len(X)} samples across {len(target_assets)} assets...")
    print(f"   >>> Global Wins: {y.sum()} ({y.mean()*100:.1f}%)")
    
    imputer = SimpleImputer(strategy='mean')
    X_imputed = imputer.fit_transform(X)
    
    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_imputed, y)
    
    # 5. SAVE
    joblib.dump({'model': model, 'imputer': imputer}, MODEL_PATH)
    
    accuracy = model.score(X_imputed, y)
    print(f"--- MULTI-ASSET BOOTSTRAP COMPLETE ---")
    print(f"Combined Brain created with {accuracy:.2%} accuracy.")
    
    # 6. SYNC TO CLOUD (V71)
    sync_model_metadata(
        version="v1.2-multi-asset",
        accuracy=accuracy,
        samples=len(X),
        features=FEATURE_COLS
    )

if __name__ == "__main__":
    bootstrap_brain()
