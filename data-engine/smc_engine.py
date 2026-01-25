
import pandas as pd
import numpy as np

class SMCEngine:
    def __init__(self):
        self.is_active = True

    def detect_fvg(self, df: pd.DataFrame):
        """
        Detects Fair Value Gaps (FVG).
        A 3-candle pattern where there's a gap between Candle 1 and Candle 3.
        """
        if len(df) < 3: return {"bullish": False, "bearish": False}
        
        # Look at the last 3 candles
        c1 = df.iloc[-3]
        c2 = df.iloc[-2]
        c3 = df.iloc[-1]
        
        bullish_fvg = c1['high'] < c3['low']
        bearish_fvg = c1['low'] > c3['high']
        
        return {
            "bullish": bullish_fvg,
            "bearish": bearish_fvg,
            "top": c3['low'] if bullish_fvg else (c1['low'] if bearish_fvg else 0),
            "bottom": c1['high'] if bullish_fvg else (c3['high'] if bearish_fvg else 0)
        }

    def detect_ob(self, df: pd.DataFrame):
        """
        Detects Order Blocks (OB).
        Bullish OB: Last bearish candle before a strong upward move.
        Bearish OB: Last bullish candle before a strong downward move.
        """
        if len(df) < 5: return {"bullish": False, "bearish": False}
        
        # Simple Logic: Check if price just broke a recent high/low with momentum
        last_price = df.iloc[-1]['close']
        prev_highs = df['high'].iloc[-10:-1].max()
        prev_lows = df['low'].iloc[-10:-1].min()
        
        # Bullish OB check
        # If we just broke a recent high, the last bearish candle in the dip is the OB
        bullish_ob = False
        if last_price > prev_highs:
            # Look for the last bearish candle
            for i in range(len(df)-2, 0, -1):
                if df.iloc[i]['close'] < df.iloc[i]['open']:
                    # We found a candidate, check if it's within a reasonable distance
                    if (last_price - df.iloc[i]['low']) / last_price < 0.05:
                        bullish_ob = True
                        break
        
        # Bearish OB check
        bearish_ob = False
        if last_price < prev_lows:
            for i in range(len(df)-2, 0, -1):
                if df.iloc[i]['close'] > df.iloc[i]['open']:
                    if (df.iloc[i]['high'] - last_price) / last_price < 0.05:
                        bearish_ob = True
                        break
                        
        return {"bullish": bullish_ob, "bearish": bearish_ob}

    def analyze(self, df: pd.DataFrame):
        """Main analysis entry point."""
        if df.empty: return {}
        
        fvg = self.detect_fvg(df)
        ob = self.detect_ob(df)
        
        return {
            "fvg_bullish": fvg['bullish'],
            "fvg_bearish": fvg['bearish'],
            "ob_bullish": ob['bullish'],
            "ob_bearish": ob['bearish'],
            "fvg_levels": [fvg['bottom'], fvg['top']] if (fvg['bullish'] or fvg['bearish']) else []
        }

smc_engine = SMCEngine()
