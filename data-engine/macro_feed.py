import yfinance as yf
import time
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MacroBrain")

class MacroBrain:
    def __init__(self):
        self.dxy_ticker = "DX-Y.NYB"
        self.spx_ticker = "^GSPC"
        self.cache_duration = 300  # 5 minutes
        self.last_fetch = 0
        self.cached_sentiment = "NEUTRAL"
        self.cached_data = {}

    def fetch_data(self):
        """
        V300: CRYPTO-NATIVE PROXY (Option A)
        Uses BTC/USDT as a real-time proxy for Macro Sentiment to avoid YFinance IP blocks.
        Logic: Inverse Correlation (BTC Down = DXY Up = Risk Off).
        """
        try:
            current_time = time.time()
            if current_time - self.last_fetch < self.cache_duration:
                return self.cached_data

            import requests
            import random
            
            # Fetch BTC Data Source (Unblockable)
            url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
            res = requests.get(url, timeout=5)
            data = res.json()
            
            btc_change = float(data['priceChangePercent'])
            btc_price = float(data['lastPrice'])
            
            logger.info(f"   [MACRO PROXY] BTC Change: {btc_change}% (Source: Binance)")

            # SIMULATE DXY & SPX based on BTC (Inverse Correlation)
            # If BTC is UP, Risk is ON -> DXY Drops, SPX Rises
            # If BTC is DOWN, Risk is OFF -> DXY Rises, SPX Drops
            
            # DXY = Negative 10% of BTC move (dampened)
            # SPX = Positive 30% of BTC move (correlated)
            
            sim_dxy_change = (btc_change * -0.1) + random.uniform(-0.05, 0.05)
            sim_spx_change = (btc_change * 0.3) + random.uniform(-0.1, 0.1)
            
            # Base Levels (Approximate)
            dxy_base = 104.50
            spx_base = 5600.00
            
            self.cached_data = {
                "dxy_price": dxy_base * (1 + (sim_dxy_change/100)),
                "dxy_change": sim_dxy_change,
                "spx_price": spx_base * (1 + (sim_spx_change/100)),
                "spx_change": sim_spx_change,
                "timestamp": current_time,
                "proxy_source": "BTC_CORRELATION"
            }
            
            self.last_fetch = current_time
            self._analyze_sentiment()
            
            logger.info(f"   [MACRO] Proxy Active. Risk: {self.cached_sentiment} (Derived from BTC {btc_change}%)")
            return self.cached_data
            
        except Exception as e:
            logger.error(f"   [MACRO] Error fetching proxy data: {e}. Using Simulation.")
            # Fallback Simulation if even Binance fails
            return {
                "dxy_price": 104.50,
                "dxy_change": 0.01,
                "spx_price": 5000.00,
                "spx_change": 0.01,
                "timestamp": time.time()
            }

    def _analyze_sentiment(self):
        """Determines RISK_ON or RISK_OFF based on DXY trend."""
        if not self.cached_data:
            self.cached_sentiment = "NEUTRAL"
            return

        dxy_chg = self.cached_data.get("dxy_change", 0)
        spx_chg = self.cached_data.get("spx_change", 0)

        # Logic: 
        # Strong DXY (> 0.3%) usually means Risk-Off for Crypto.
        # Strong SPX Drop (< -0.5%) means Risk-Off.
        
        if dxy_chg > 0.3 or spx_chg < -0.6:
            self.cached_sentiment = "RISK_OFF"
        elif dxy_chg < -0.2 and spx_chg > 0.1:
            self.cached_sentiment = "RISK_ON"
        else:
            self.cached_sentiment = "NEUTRAL"
            
        logger.info(f"   [MACRO] Sentiment Updated: {self.cached_sentiment}")

    def get_macro_sentiment(self):
        """Returns 'RISK_ON', 'RISK_OFF', or 'NEUTRAL'."""
        # Ensure data is fresh
        if time.time() - self.last_fetch > self.cache_duration:
            self.fetch_data()
            
        return self.cached_sentiment

# Singleton
macro_brain = MacroBrain()
