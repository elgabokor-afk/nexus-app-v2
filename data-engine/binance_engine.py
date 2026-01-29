import os
import ccxt
import requests
import json
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
                # V3001: RESTORED Explicit Sync (User has >3s clock drift)
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

    def _map_symbol_to_kraken(self, symbol):
        """Standardizes symbols for Kraken (USDT -> USD)."""
        if not symbol: return symbol
        return symbol.replace("/USDT", "/USD")

    def _fetch_coincap_ticker(self, symbol):
        """Tier-3 Fallback: CoinCap (No Geo-Block)."""
        try:
            # Map BTC/USDT -> bitcoin
            base = symbol.split('/')[0].lower()
            # Mapping common coins
            # A robust map would be better, but heuristic for top coins:
            asset_id = base
            if base == 'btc': asset_id = 'bitcoin'
            elif base == 'eth': asset_id = 'ethereum'
            elif base == 'sol': asset_id = 'solana'
            elif base == 'bnb': asset_id = 'binance-coin'
            elif base == 'xrp': asset_id = 'xrp'
            elif base == 'doge': asset_id = 'dogecoin'
            
            url = f"https://api.coincap.io/v2/assets/{asset_id}"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()['data']
                price = float(data['priceUsd'])
                return {
                    'symbol': symbol,
                    'last': price,
                    'bid': price,
                    'ask': price,
                    'percentage': float(data['changePercent24Hr'])
                }
        except Exception as e:
            print(f"   [COINCAP] Error: {e}")
        return None

    # V2600: MARKET DATA CAPABILITIES (Kraken Primary)
    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100):
        """Fetch historical candle data (V2600: Kraken Primary)."""
        kraken_symbol = self._map_symbol_to_kraken(symbol)
        try:
            # Try Kraken First
            return self.fallback_exchange.fetch_ohlcv(kraken_symbol, timeframe, limit=limit)
        except Exception as e:
            print(f"   [KRAKEN] Fetch OHLCV failed for {kraken_symbol}: {e}. Falling back to Binance...")
            try:
                return self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            except Exception as b_err:
                if "451" in str(b_err) or "Service unavailable" in str(b_err):
                     print(f"   [BINANCE] Geo-Block Detected (451). Switching to CoinGecko (OHLC).")
                     return self._fetch_coincap_ohlcv(symbol, timeframe, limit)
                     
                print(f"   [BINANCE] Fallback Fetch OHLCV failed for {symbol}: {b_err}")
                return self._fetch_coincap_ohlcv(symbol, timeframe, limit) # Last resort

    def fetch_ticker(self, symbol):
        """Fetch real-time price info (V2600: Kraken Primary)."""
        kraken_symbol = self._map_symbol_to_kraken(symbol)
        try:
            # Try Kraken First
            return self.fallback_exchange.fetch_ticker(kraken_symbol)
        except Exception as e:
            print(f"   [KRAKEN] Fetch Ticker failed for {kraken_symbol}: {e}. Falling back to Binance...")
            try:
                # Map to Futures if needed
                if not self.exchange.markets: self.exchange.load_markets()
                
                fut_symbol = symbol
                if fut_symbol not in self.exchange.markets:
                    if f"{symbol}:USDT" in self.exchange.markets:
                        fut_symbol = f"{symbol}:USDT"
                
                return self.exchange.fetch_ticker(fut_symbol)
            except Exception as b_err:
                # V312: COINCAP FALLBACK (Geo-Block Bypass)
                if "451" in str(b_err) or "Service unavailable" in str(b_err):
                     print(f"   [BINANCE] Geo-Block Detected (451). Switching to CoinCap.")
                     return self._fetch_coincap_ticker(symbol)
                
                print(f"   [BINANCE] Fallback Fetch Ticker failed for {symbol}: {b_err}")
                return self._fetch_coincap_ticker(symbol) # Try anyway

    def _fetch_coincap_ohlcv(self, symbol, timeframe='1h', limit=100):
        """Tier-3 Fallback: CoinCap History."""
        try:
            # Map BTC/USDT -> bitcoin
            base = symbol.split('/')[0].lower()
            asset_id = base
            if base == 'btc': asset_id = 'bitcoin'
            elif base == 'eth': asset_id = 'ethereum'
            elif base == 'sol': asset_id = 'solana'
            elif base == 'bnb': asset_id = 'binance-coin'
            elif base == 'xrp': asset_id = 'xrp'
            elif base == 'doge': asset_id = 'dogecoin'
            elif base == 'ada': asset_id = 'cardano'
            
            # Map Timeframe: 5m -> m5, 1h -> h1
            interval = timeframe.replace('m', 'm').replace('h', 'h')
            if interval == '5m': interval = 'm5'
            elif interval == '15m': interval = 'm15'
            elif interval == '1h': interval = 'h1'
            elif interval == '4h': interval = 'h2' # CoinCap doesn't have h4, using h2 or fallback
            else: interval = 'h1'
            
            url = f"https://api.coincap.io/v2/assets/{asset_id}/history?interval={interval}"
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()['data']
                # CoinCap returns: { time, priceUsd, date }
                # Parse to OHLCV (Synthetic because CoinCap History is Close-Only for some endpoints? 
                # Wait, history endpoint is often close price only unless using 'candles' endpoint which requires diff API key or Poloniex etc.
                # Actually CoinCap 'candles' (open/high/low/close) is available via: 
                # GET /v2/candles?exchange=poloniex&interval=h8&baseId=ethereum&quoteId=bitcoin
                # That is complex. The /history endpoint gives PRICE.
                # If we only have price, High=Low=Close. ATR will be 0.
                # WE NEED REAL CANDLES.
                # Let's try CryptoCompare? Or assume CoinGecko?
                # CoinGecko has OHLC.
                pass 
                
            # Switch to CoinGecko for OHLC?
            # Free API: /coins/{id}/ohlc?vs_currency=usd&days=1
            print(f"   [COINCAP] Warning: History endpoint is close-only. Switching to CoinGecko for Candle Data...")
            return self._fetch_coingecko_ohlc(asset_id, timeframe)

        except Exception as e:
            print(f"   [COINCAP] Error: {e}")
        return []

    def _fetch_coingecko_ohlc(self, asset_id, timeframe):
        try:
            days = '1'
            if 'h' in timeframe: days = '7'
            
            url = f"https://api.coingecko.com/api/v3/coins/{asset_id}/ohlc?vs_currency=usd&days={days}"
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if res.status_code == 200:
                # [time, open, high, low, close]
                data = res.json()
                # Sort and Limit
                data.sort(key=lambda x: x[0])
                # Add Volume = 0 (missing in Gecko OHLC free)
                candles = [[t, o, h, l, c, 0] for (t,o,h,l,c) in data[-100:]]
                return candles
        except Exception as e:
            print(f"   [COINGECKO] Error: {e}")
        return []

    def fetch_order_book(self, symbol, limit=50):
        """Fetch L2 Order Book (V2600: Kraken Primary)."""
        kraken_symbol = self._map_symbol_to_kraken(symbol)
        try:
            # Try Kraken First
            return self.fallback_exchange.fetch_order_book(kraken_symbol, limit=limit)
        except Exception as e:
            print(f"   [KRAKEN] Fetch Order Book failed for {kraken_symbol}: {e}. Falling back to Binance...")
            try:
                return self.exchange.fetch_order_book(symbol, limit=limit)
            except Exception as b_err:
                print(f"   [BINANCE] Fallback Fetch Order Book failed for {symbol}: {b_err}")
                return None

    # V314: FUTURES SYMBOL MAPPER
    def _map_to_futures_symbol(self, symbol):
        """
        Maps generic symbols to Binance Futures format.
        BTC/USDT -> BTC/USDT:USDT (Linear)
        """
        if ":" in symbol: return symbol
        if "/USD" in symbol and "/USDT" not in symbol:
             symbol = symbol.replace("/USD", "/USDT")
        
        # Check if we need to append :USDT
        # For linear contracts, it's often safer to use the standard ID if loaded, 
        # but let's try the common suffix if simple lookup fails.
        return symbol

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

        # Map to Futures
        symbol = self._map_to_futures_symbol(symbol)

        print(f"   [BINANCE] PRE-ORDER DIAGNOSTICS (MARGIN): {symbol} | Side: {side} | Target Amount: {amount}")

        try:
            # 1. Load Markets (if not loaded)
            if not self.exchange.markets:
                print("   [BINANCE] Loading market data...")
                self.exchange.load_markets()
            
            # Check if symbol exists in markets
            if symbol not in self.exchange.markets:
                 # Try appending :USDT if missing
                 alt_symbol = f"{symbol}:USDT"
                 if alt_symbol in self.exchange.markets:
                     symbol = alt_symbol
                     print(f"   [BINANCE] Auto-Corrected Symbol to {symbol}")
                 else:
                     print(f"   [BINANCE] CRITICAL: Market {symbol} not found in Futures.")
                     return None

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
