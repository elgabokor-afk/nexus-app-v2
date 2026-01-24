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
        
        # Initialize CCXT Binance
        # options: defaultType: 'future' for USDS-M Futures
        self.exchange = ccxt.binance({
            'apiKey': self.api_key,
            'secret': self.secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future' 
            }
        })
        
        self.is_connected = False
        if self.api_key and self.secret:
            try:
                # Test connectivity by fetching balance
                self.exchange.fetch_balance()
                self.is_connected = True
                print(f"   [BINANCE] Connected successfully in {self.mode} mode.")
            except Exception as e:
                print(f"   [BINANCE] Connectivity error: {e}")

    def get_live_balance(self):
        """Fetch real USDT balance from Binance Futures."""
        if not self.is_connected: return 0
        try:
            balance = self.exchange.fetch_balance()
            return float(balance['total']['USDT'])
        except Exception as e:
            print(f"   [BINANCE] Error fetching balance: {e}")
            return 0

    def execute_market_order(self, symbol, side, amount, leverage=10):
        """
        Executes a real MARKET order on Binance.
        side: 'buy' or 'sell'
        amount: Quantity in base asset (e.g. BTC)
        """
        if self.mode != "LIVE":
            print(f"   [BINANCE] Blocked: Trading mode is {self.mode}. Order simulated.")
            return {"status": "SIMULATED", "id": "paper_v100"}

        if not self.is_connected:
            print("   [BINANCE] Error: Not connected to API.")
            return None

        try:
            # 1. Set Leverage
            # Binance requires setting leverage before opening a position
            self.exchange.set_leverage(leverage, symbol)
            
            # 2. Create Order
            order = self.exchange.create_market_order(symbol, side, amount)
            print(f"   [BINANCE] LIVE ORDER EXECUTED: {side} {amount} {symbol}")
            return order
        except Exception as e:
            print(f"   [BINANCE] Execution Error: {e}")
            return None

# Singleton for easy access
live_trader = BinanceTrader()
