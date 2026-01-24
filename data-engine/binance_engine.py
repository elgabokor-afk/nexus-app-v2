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
                'defaultType': 'future',
                'adjustForTimeDifference': True,
                'recvWindow': 10000 
            }
        })
        
        
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
            # 1. Load Markets (if not loaded)
            if not self.exchange.markets:
                self.exchange.load_markets()

            # 2. Precision Handling
            clean_amount = self.exchange.amount_to_precision(symbol, amount)
            
            # 3. Set Leverage & Execute
            # Binance requires setting leverage before opening a position
            try:
                self.exchange.set_leverage(leverage, symbol)
            except Exception as lev_err:
                print(f"   [BINANCE] Leverage warning: {lev_err}")

            order = self.exchange.create_market_order(symbol, side, clean_amount)
            print(f"   [BINANCE] LIVE ORDER EXECUTED: {side} {clean_amount} {symbol}")
            return order
            print(f"   [BINANCE] Execution Error: {e}")
            return None

    def get_open_positions(self):
        """Fetch all currently open positions from Binance."""
        if not self.is_connected: return []
        try:
            positions = self.exchange.fetch_positions()
            # Filter for active positions only
            active = [p for p in positions if float(p['contracts']) > 0]
            return active
        except Exception as e:
            print(f"   [BINANCE] Error fetching positions: {e}")
            return []

# Singleton for easy access
live_trader = BinanceTrader()
