import os
import ccxt
from dotenv import load_dotenv

# Load credentials
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

class BinanceTrader:
    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.secret = os.getenv("BINANCE_SECRET")
        self.mode = os.getenv("TRADING_MODE", "PAPER")
        
        # V311: PROXY SUPPORT
        self.proxy = os.getenv("BINANCE_PROXY")
        
        # Initialize CCXT Binance
        binance_config = {
            'apiKey': self.api_key,
            'secret': self.secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap', # V600: BINANCE FUTURES (USDT-M)
                'adjustForTimeDifference': True,
                'recvWindow': 60000 
            }
        }
        
        if self.proxy:
            binance_config['proxies'] = {'https': self.proxy, 'http': self.proxy}
            print(f"   [BINANCE] Proxy Enabled: {self.proxy}")

        self.exchange = ccxt.binance(binance_config)
        
        # V311: RESILIENT DATA LAYER (Kraken Fallback for 451 Errors)
        self.fallback_exchange = ccxt.kraken({'enableRateLimit': True})
        
        
        self.is_connected = False
        if self.api_key and self.secret:
            try:
                # Explicitly sync time to prevent timestamp errors
                time_offset = self.exchange.load_time_difference()
                print(f"   [BINANCE] Time Sync Active (Offset: {time_offset}ms)")
                
                # Test connectivity by fetching balance
                self.exchange.fetch_balance()
                self.is_connected = True
                print(f"   [BINANCE] Connected successfully in {self.mode} mode.")
            except Exception as e:
                print(f"   [BINANCE] Connectivity error: {e}")

    def get_live_balance(self):
        """Fetch real USDT balance from Binance Futures Wallet."""
        if not self.is_connected: return 0
        try:
            # V600: Fetching swap/futures balance
            balance = self.exchange.fetch_balance({'type': 'swap'})
            return float(balance.get('USDT', {}).get('free', balance['total'].get('USDT', 0)))
        except Exception as e:
            print(f"   [BINANCE] Error fetching futures balance: {e}")
            return 0

    def get_margin_level(self):
        """Fetch current margin level (Risk Ratio) for Spot Margin."""
        if not self.is_connected: return 999.0
        try:
            # V215: Check health ratio (Total Assets / Total Debt)
            balance = self.exchange.fetch_balance({'type': 'margin'})
            level = float(balance['info'].get('marginLevel', 999.0))
            return level
        except Exception as e:
            print(f"   [BINANCE] Error fetching margin level: {e}")
            return 999.0

    # V310: MARKET DATA CAPABILITIES
    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100):
        """Fetch historical candle data (V311: with Kraken Fallback)."""
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        except Exception as e:
            if "451" in str(e):
                print(f"   [V311 FALLBACK] Binance Blocked (451). Trying Kraken for {symbol}...")
                # Kraken uses /USD instead of /USDT for some pairs, but CCXT handles it well
                return self.fallback_exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            print(f"   [BINANCE] Error fetching OHLCV for {symbol}: {e}")
            return []

    def fetch_ticker(self, symbol):
        """Fetch real-time price info (V311: with Kraken Fallback)."""
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            if "451" in str(e):
                print(f"   [V311 FALLBACK] Binance Blocked (451). Trying Kraken price for {symbol}...")
                return self.fallback_exchange.fetch_ticker(symbol)
            print(f"   [BINANCE] Error fetching ticker for {symbol}: {e}")
            return None

    def fetch_order_book(self, symbol, limit=50):
        """Fetch L2 Order Book (V311: with Kraken Fallback)."""
        try:
            return self.exchange.fetch_order_book(symbol, limit=limit)
        except Exception as e:
            if "451" in str(e):
                print(f"   [V311 FALLBACK] Binance Blocked (451). Trying Kraken books for {symbol}...")
                return self.fallback_exchange.fetch_order_book(symbol, limit=limit)
            print(f"   [BINANCE] Error fetching order book for {symbol}: {e}")
            return None

    def execute_market_order(self, symbol, side, amount, leverage=1):
        """
        Executes a real MARKET order on Binance Margin.
        Note: Spot Margin uses collateral-based leverage.
        """
        if self.mode != "LIVE":
            print(f"   [BINANCE] Blocked: Trading mode is {self.mode}. Order simulated.")
            return {"status": "SIMULATED", "id": "paper_v100"}

        if not self.is_connected:
            print("   [BINANCE] Error: Not connected to API.")
            return None

        print(f"   [BINANCE] PRE-ORDER DIAGNOSTICS (MARGIN): {symbol} | Side: {side} | Target Amount: {amount}")

        try:
            # 1. Load Markets (if not loaded)
            if not self.exchange.markets:
                print("   [BINANCE] Loading market data...")
                self.exchange.load_markets()

            # V2500: Leverage Upgrade (Cap raised to 10x)
            target_leverage = min(leverage, 10)
            try:
                self.exchange.set_leverage(target_leverage, symbol)
                print(f"   [BINANCE] Leverage set to {target_leverage}x for {symbol}")
            except Exception as lv_err:
                print(f"   [BINANCE] Leverage warning: {lv_err}")

            # 2. Precision Handling
            clean_amount = self.exchange.amount_to_precision(symbol, amount)
            print(f"   [BINANCE] Precision Adjustment: {amount} -> {clean_amount}")
            
            if float(clean_amount) <= 0:
                print(f"   [BINANCE] ERROR: Amount {clean_amount} is too small.")
                return None

            # 4. Final Execution (V600: Standard Futures Market Order)
            print(f"   [BINANCE] EXECUTING FUTURES ORDER: {side.upper()} {clean_amount} {symbol}")
            order = self.exchange.create_market_order(symbol, side, clean_amount)
            print(f"   [BINANCE] SUCCESS: Order ID {order.get('id')} executed on Futures.")
            return order
        except Exception as e:
            print(f"   [BINANCE] CRITICAL MARGIN ERROR: {e}")
            if hasattr(e, 'feedback'): print(f"   [BINANCE] API Feedback: {e.feedback}")
            return None

    def get_open_positions(self):
        """
        Fetch active positions for Binance Futures (swap).
        """
        if not self.is_connected: return []
        try:
            # V600: Fetching real futures positions
            positions = self.exchange.fetch_positions()
            active_positions = []
            
            for pos in positions:
                contracts = float(pos.get('contracts', 0) or 0)
                if contracts > 0:
                    active_positions.append({
                        'symbol': pos['symbol'],
                        'contracts': contracts,
                        'side': pos['side'],
                        'entryPrice': float(pos.get('entryPrice', 0) or 0),
                        'unrealizedPnl': float(pos.get('unrealizedPnl', 0) or 0)
                    })
            return active_positions
        except Exception as e:
            print(f"   [BINANCE] Error fetching futures positions: {e}")
            return []

# Singleton for easy access
live_trader = BinanceTrader()
