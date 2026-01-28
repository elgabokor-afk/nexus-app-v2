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
        """Fetches latest DXY and SPX data from Yahoo Finance."""
        try:
            current_time = time.time()
            if current_time - self.last_fetch < self.cache_duration:
                return self.cached_data

            logger.info("   [MACRO] Fetching global market data (DXY, SPX)...")
            
            # Fetch DXY
            dxy = yf.Ticker(self.dxy_ticker).history(period="5d", interval="1d")
            spx = yf.Ticker(self.spx_ticker).history(period="5d", interval="1d")
            
            if dxy.empty or spx.empty:
                logger.warning("   [MACRO] Failed to fetch macro data (Empty DF).")
                return self.cached_data

            dxy_change = ((dxy['Close'].iloc[-1] - dxy['Close'].iloc[-2]) / dxy['Close'].iloc[-2]) * 100
            spx_change = ((spx['Close'].iloc[-1] - spx['Close'].iloc[-2]) / spx['Close'].iloc[-2]) * 100
            
            self.cached_data = {
                "dxy_price": dxy['Close'].iloc[-1],
                "dxy_change": dxy_change,
                "spx_price": spx['Close'].iloc[-1],
                "spx_change": spx_change,
                "timestamp": current_time
            }
            
            self.last_fetch = current_time
            self._analyze_sentiment()
            
            logger.info(f"   [MACRO] DXY: {self.cached_data['dxy_price']:.2f} ({dxy_change:+.2f}%) | SPX: {spx_change:+.2f}%")
            return self.cached_data
            
        except Exception as e:
            logger.error(f"   [MACRO] Error fetching data: {e}")
            return self.cached_data

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
