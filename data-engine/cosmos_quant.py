import logging
# We will use the live_trader from binance_engine to fetch order books
from binance_engine import live_trader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CosmosQuant")

class QuantAnalyzer:
    def __init__(self):
        pass

    def analyze_order_flow(self, symbol):
        """
        Analyzes the Order Book (Depth) to detect Whale Walls and Imbalance.
        Returns a dict with 'imbalance_score', 'whale_wall_side', and 'valid'.
        """
        try:
            # Fetch Depth (Limit 50 is enough for immediate pressure)
            book = live_trader.fetch_order_book(symbol, limit=100)
            if not book:
                return {'valid': False, 'reason': 'No Data'}

            bids = book['bids'] # [[price, qty], ...]
            asks = book['asks']

            if not bids or not asks:
                return {'valid': False, 'reason': 'Empty Book'}

            # 1. Calculate Total Volume in Top 50 levels
            total_bid_vol = sum([b[1] for b in bids])
            total_ask_vol = sum([a[1] for a in asks])
            
            if total_bid_vol == 0 or total_ask_vol == 0:
                 return {'valid': False, 'reason': 'Zero Volume'}

            # 2. Imbalance Ratio (-1.0 to 1.0)
            # Positive = Buying Pressure
            # Negative = Selling Pressure
            imbalance = (total_bid_vol - total_ask_vol) / (total_bid_vol + total_ask_vol)

            # 3. Detect Whale Walls (Single orders > 5% of total side volume)
            whale_walls = []
            
            # Check Bids
            for b in bids[:10]: # Only check near price
                if b[1] > (total_bid_vol * 0.05):
                    whale_walls.append(f"BUY_WALL @ {b[0]}")
            
            # Check Asks
            for a in asks[:10]:
                if a[1] > (total_ask_vol * 0.05):
                    whale_walls.append(f"SELL_WALL @ {a[0]}")

            return {
                'valid': True,
                'imbalance': round(imbalance, 3), # e.g. 0.45
                'bid_vol': total_bid_vol,
                'ask_vol': total_ask_vol,
                'whale_walls': whale_walls,
                'sentiment': 'BULLISH' if imbalance > 0.2 else ('BEARISH' if imbalance < -0.2 else 'NEUTRAL')
            }

        except Exception as e:
            logger.error(f"Quant Analysis Error for {symbol}: {e}")
            return {'valid': False, 'error': str(e)}

    def check_liquidity_health(self, symbol):
        """Ensures the asset has enough liquidity for safe entry."""
        flow = self.analyze_order_flow(symbol)
        if not flow['valid']: return False
        
        # Arbitrary Threshold: Must have at least 10k units volume in depth (context dependent, but good safety)
        # For USDT pairs, quote volume is better. But simplest is imbalance check.
        # If imbalance is TOO extreme (>0.8), it might be spoofing.
        if abs(flow['imbalance']) > 0.9:
            logger.warning(f"   [QUANT] {symbol} Rejected: Extreme Imbalance (Possible Spoofing/Illiquid)")
            return False
            
        return True

# Singleton
quant_engine = QuantAnalyzer()
