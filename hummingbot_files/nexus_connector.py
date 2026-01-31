
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
from hummingbot.core.data_type.common import OrderType
from decimal import Decimal
import os
from supabase import create_client, Client

# --- SUPABASE CONFIG ---
# In Docker, these will be environment variables
SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

class NexusConnector(ScriptStrategyBase):
    """
    Nexus App V2 Connector
    Runs a simple market making strategy and pushes updates to Supabase.
    """
    
    # V411: Lock to Binance Margin Connector
    markets = {"binance_margin": {"BTC-USDT", "SOL-USDT", "ETH-USDT"}}
    
    def __init__(self, connectors):
        super().__init__(connectors)
        self.supabase: Client = None
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                self.log("Connected to Supabase successfully.")
            except Exception as e:
                self.log(f"Failed to connect to Supabase: {e}")
        else:
            self.log("Supabase credentials missing.")

    def on_tick(self):
        # 1. Fetch Price
        for connector_name, connector in self.connectors.items():
            for trading_pair in self.markets[connector_name]:
                best_bid = connector.get_price(trading_pair, True)
                best_ask = connector.get_price(trading_pair, False)
                mid_price = (best_bid + best_ask) / 2
                
                # 2. Logic: If price ends in .00 (Simulated Logic), send a signal
                # This is a placeholder for real strategy logic (e.g. Bollinger Bands)
                # In a real bot, you'd place orders here:
                # self.buy(connector_name, trading_pair, amount, OrderType.LIMIT, price)
                
                # 3. Push "Heartbeat" / Signal to Dashboard every ~10 ticks (approx 10s)
                if self.current_timestamp % 10 < 1: 
                    self.push_to_dashboard(trading_pair, float(mid_price))

    def push_to_dashboard(self, pair, price):
        if not self.supabase:
            return

        # Map pair format (HB uses BTC-USDT, Dashboard uses BTC/USDT)
        display_symbol = pair.replace("-", "/")
        
        # Simulated Signal for Dashboard Visualization
        # In production, this would only fire on REAL trade events
        data = {
            "symbol": display_symbol,
            "price": price,
            "rsi": 50.0, # Placeholder
            "signal_type": "HB MARKET MAKING",
            "confidence": 100,
            "stop_loss": price * 0.99,
            "take_profit": price * 1.01
        }
        
        try:
            self.supabase.table("market_signals").insert(data).execute()
            self.log(f"Pushed {display_symbol} status to Dashboard.")
        except Exception as e:
            self.log(f"Supabase Insert Error: {e}")
