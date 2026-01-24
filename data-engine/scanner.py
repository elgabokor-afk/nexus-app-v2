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

    # V4 UPGRADE: QUANTITATIVE SCORING
    # Fetch Order Book for Deep Analysis
    order_book = fetch_order_book(latest['symbol'] if 'symbol' in latest else df.attrs.get('symbol')) 
    # Note: df doesn't store symbol by default, we need to pass it or assume main loop handles it.
    # We will fetch book inside main loop to avoid passing too many args, or fetch here if we refactor.
    # Refactoring: Let's fetch OB inside here to keep logic encapsulated, but we need symbol.
    # Quick fix: Pass symbol to analyze_market or rely on main. 
    # Let's adjust main loop to pass symbol to verify. For now, we return partial analysis and let main finish it?
    # No, cleaner to pass symbol. Changing signature.
    
    # ... Wait, changing signature might break tests. 
    # Let's assume 'analyze_market' is called with symbol context. 
    # Actually, let's keep it simple: We do the technicals here, and add Quant metrics in the Main loop or 
    # improve this function to accept symbol. I'll update the main call to pass symbol.
    
    return {
        'timestamp': latest['timestamp'],
        'price': price,
        'rsi': round(rsi, 2),
        'ema_200': ema_200,
        'atr': atr,
        'volume': volume,
        'vol_ma': vol_ma,
        # Techncial Signal (Base)
        'tech_score': score 
    }

def analyze_quant_signal(symbol, tech_analysis):
    """
    Combines Technicals (RSI/EMA) with Quant Data (Order Book)
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
    
    # 2. WEIGHTED SCORE CALCULATION
    # Components:
    # A. RSI (0-100 normalized to 0-1) -> 30%
    # B. Trend (Price vs EMA) -> 20%
    # C. Imbalance (-1 to 1 normalized to 0-1) -> 30%
    # D. Volume (Ratio) -> 20%
    
    # Normalize RSI (Bearish < 30, Bullish > 70? No, standard logic)
    # Let's align everything to "Bullishness" (0 to 1)
    
    # RSI Score: Low RSI is Bullish (Purchase opp), High is Bearish
    # 30 -> 1.0, 70 -> 0.0
    rsi_score = 0.5
    if rsi < 30: rsi_score = 1.0
    elif rsi > 70: rsi_score = 0.0
    else: rsi_score = 1.0 - ((rsi - 30) / 40) # Linear decay 30-70
    
    # Trend Score
    trend_score = 1.0 if price > tech_analysis['ema_200'] else 0.0
    
    # Imbalance Score (-1 to 1 -> 0 to 1)
    imb_score = (imbalance + 1) / 2
    
    # Volume Score
    vol_ratio = tech_analysis['volume'] / tech_analysis['vol_ma'] if tech_analysis['vol_ma'] > 0 else 1
    vol_score = min(vol_ratio / 2, 1.0) # Cap at 2x volume
    
    # FINAL WEIGHTED SCORE
    final_score = (rsi_score * 0.30) + (trend_score * 0.20) + (imb_score * 0.30) + (vol_score * 0.20)
    final_confidence = int(final_score * 100)
    
    # DETERMINE SIGNAL
    signal_type = "NEUTRAL"
    if final_confidence >= 75: signal_type = "STRONG BUY"
    elif final_confidence >= 60: signal_type = "MODERATE BUY"
    elif final_confidence <= 25: signal_type = "STRONG SELL" # Imbalance/Trend strongly negative
    elif final_confidence <= 40: signal_type = "MODERATE SELL"
    
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
        'depth_score': int(vol_score * 100) # Proxy for depth/volume quality
    }

from db import insert_signal, insert_analytics, log_error
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
                techs = analyze_market(df) # Returns basic tech metrics
                
                if techs:
                    # Upgrade to V4 Analysis
                    quant_signal = analyze_quant_signal(symbol, techs)
                    
                    if quant_signal:
                        print(f"[{symbol}] Price: {quant_signal['price']} | RSI: {quant_signal['rsi']} | Imb: {quant_signal['imbalance']}")
                        print(f"   >>> V4 SIGNAL: {quant_signal['signal']} ({quant_signal['confidence']}%)")
                        
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
                                depth_score=quant_signal['depth_score']
                            )
                        
                        # Broadcast via Telegram (V3 style for now, upgrade next)
                        tg.send_signal(
                            symbol=symbol,
                            signal_type=quant_signal['signal'],
                            price=float(quant_signal['price']),
                            confidence=int(quant_signal['confidence']),
                            stop_loss=float(quant_signal['stop_loss']),
                            take_profit=float(quant_signal['take_profit'])
                        )
                    else:
                        print(f"   --- No Signal ({symbol})")
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
