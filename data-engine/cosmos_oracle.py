import os
import time
import pandas as pd
import ccxt
from dotenv import load_dotenv
from cosmos_engine import brain
from db import insert_oracle_insight, log_error, insert_signal, insert_analytics

load_dotenv(dotenv_path="../.env.local")

# KRAKEN CONFIG
exchange_config = {
    'apiKey': os.getenv('KRAKEN_API_KEY'),
    'secret': os.getenv('KRAKEN_SECRET_KEY'),
    'enableRateLimit': True,
}
exchange = ccxt.kraken(exchange_config)

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

def run_oracle_step(symbol='BTC/USD'):
    """
    V40 Oracle Loop:
    1. Fetch 1m Candles
    2. Compute Indicators
    3. Generate BLM Reasoning
    4. Sync to Vercel/Supabase
    """
    try:
        # 1. FETCH 1m DATA
        bars = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=100)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # 2. COMPUTE TECHS
        df['RSI'] = calculate_rsi(df['close'])
        df['EMA_200'] = calculate_ema(df['close'])
        macd, sig, hist = calculate_macd(df['close'])
        
        # Calculate Imbalance (requires fetch_order_book)
        # For the Oracle Pulse we will simplify to Price/EMA/RSI/MACD
        latest = df.iloc[-1]
        
        features = {
            'price': latest['close'],
            'rsi_value': latest['RSI'],
            'ema_200': latest['EMA_200'],
            'histogram': hist.iloc[-1],
            'macd_line': macd.iloc[-1],
            'imbalance_ratio': 0 # Placeholder for this 1m pulse
        }
        
        # 3. BLM ANALYSIS
        prob = brain.predict_success(features)
        trend = brain.get_trend_status(features)
        reasoning = brain.generate_reasoning(features, prob)
        
        # Decide if we should scalp
        # V60: We define 1m scalping as a STRONG BUY or STRONG SELL
        signal_type = "STRONG BUY" if prob >= 0.90 and trend == "BULLISH" else \
                      "STRONG SELL" if prob >= 0.90 and trend == "BEARISH" else "NEUTRAL"

        # 4. SYNC TO SUPABASE
        print(f"[{time.strftime('%H:%M:%S')}] ORACLE | {symbol} | {trend} | Prob: {prob*100:.1f}%")
        
        # 5. EMIT SCALP SIGNAL (V60)
        # Only if confidence is 90% and it aligns with trend
        if signal_type != "NEUTRAL":
            print(f"      !!! SCALP OPPORTUNITY DETECTED: {signal_type} !!!")
            
            # V61: Use wider ATR targets to allow for corrections
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
                    imbalance_ratio=0, # Simplified
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
                "type": "SCALP_SCAN"
            }
        )
        
    except Exception as e:
        print(f"Oracle Error: {e}")
        log_error("COSMOS_ORACLE", e, "ERROR")

if __name__ == "__main__":
    print("--- COSMOS ORACLE V40 (BLM) STARTED ---")
    print("Monitoring 1m Candles... Syncing to Vercel via Supabase (30s Pulse).")
    while True:
        run_oracle_step()
        time.sleep(30) # Increased frequency for better real-time feel (V62)
