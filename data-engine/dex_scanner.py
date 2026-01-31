
import requests
import json
import time

class DEXScanner:
    def __init__(self):
        # Public Endpoints
        self.jup_api = "https://quote-api.jup.ag/v6/quote"
        self.hyperliquid_api = "https://api.hyperliquid.xyz/info"
        self.dydx_api = "https://api.dydx.exchange/v3/orderbook"
        
        # Mapping for common assets to Solana Mint Addresses (for Jupiter)
        self.mints = {
            "SOL": "So11111111111111111111111111111111111111112",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
            "WIF": "EKpQGSJtjjtZkXXJ3sbm666S6EVE6s9pt3pG1iK36j8", # Dogwifhat
            "BONK": "DezXAZ8z7PnrnMcjz2wXUXSR6XL9Y5S5vX911T2GDFJC"
        }

    def get_solana_liquidity_depth(self, input_mint, output_mint, amount_usd=10000):
        """
        Uses Jupiter API to estimate liquidity depth via Price Impact.
        Input amount is in atomic units (lamports for SOL, units for USDC).
        """
        # Simplistic conversion: 10k USD roughly
        # For USDC (6 decimals)
        amount = amount_usd * 1000000 
        
        url = f"{self.jup_api}?inputMint={input_mint}&outputMint={output_mint}&amount={amount}&slippageBps=50"
        
        try:
            res = requests.get(url, timeout=5)
            data = res.json()
            if 'priceImpactPct' in data:
                return float(data['priceImpactPct'])
            return None
        except Exception as e:
            # print(f"Jupiter API Error: {e}")
            return None

    def get_dydx_orderbook(self, symbol="BTC-USD"):
        """
        Fetches Order Book from dYdX (public V3 API).
        """
        url = f"{self.dydx_api}/{symbol}"
        try:
            res = requests.get(url, timeout=5)
            return res.json()
        except Exception as e:
            return None

    def get_hyperliquid_orderbook(self, symbol="BTC"):
        """
        Fetches L2 Order Book from Hyperliquid (public API).
        """
        payload = {
            "type": "l2Book",
            "coin": symbol
        }
        try:
            res = requests.post(self.hyperliquid_api, json=payload, timeout=5)
            return res.json()
        except Exception as e:
            print(f"Hyperliquid API Error: {e}")
            return None

    def calculate_dex_force(self, symbol):
        """
        Aggregates DEX data into a unified 'Force' metric (-1 to 1).
        - Impact on SOL/USDC (Reverse proxy for liquidity)
        - Hyperliquid Order Imbalance
        """
        force = 0
        
        # 1. Hyperliquid Check (if available)
        hl_book = self.get_hyperliquid_orderbook(symbol)
        if hl_book and 'levels' in hl_book:
            # Simple imbalance: (Bid Volume - Ask Volume) / Total Volume
            bids = sum([float(l['sz']) for l in hl_book['levels'][0]])
            asks = sum([float(l['sz']) for l in hl_book['levels'][1]])
            if (bids + asks) > 0:
                hl_imb = (bids - asks) / (bids + asks)
                force += hl_imb * 0.4 # 40% weight
        
        # 2. dYdX Check
        dydx_symbol = f"{symbol}-USD"
        dydx_book = self.get_dydx_orderbook(dydx_symbol)
        if dydx_book and 'bids' in dydx_book:
            bids = sum([float(l['amount']) for l in dydx_book['bids'][:10]])
            asks = sum([float(l['amount']) for l in dydx_book['asks'][:10]])
            if (bids + asks) > 0:
                dydx_imb = (bids - asks) / (bids + asks)
                force += dydx_imb * 0.4 # 40% weight

        # 3. Solana Check (using SOL as proxy if asset is SOL or correlated)
        if symbol in ["SOL", "SOL/USDT"]:
            impact = self.get_solana_liquidity_depth(self.mints["SOL"], self.mints["USDC"])
            if impact is not None:
                # High impact = Negative force (liquidity drain)
                force -= impact * 5 # Weighted impact
                
        return round(force, 2)

    def get_global_force(self, symbol, cex_imbalance, whale_sentiment=0):
        """
        Synthesizes CEX, DEX, and Whale data into a single -1 to 1 score.
        """
        dex_f = self.calculate_dex_force(symbol)
        
        # Weighted Average
        # 40% CEX, 40% DEX, 20% Whale Flow
        global_score = (cex_imbalance * 0.4) + (dex_f * 0.4) + (whale_sentiment * 0.2)
        
        return round(global_score, 2)

if __name__ == "__main__":
    scanner = DEXScanner()
    print(f"Hyperliquid BTC Force: {scanner.calculate_dex_force('BTC')}")
    print(f"dYdX BTC Force: {scanner.get_dydx_orderbook('BTC-USD') is not None}")
