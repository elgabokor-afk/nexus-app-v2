import os
import ccxt
from dotenv import load_dotenv

# Load credentials
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

def audit_wallet():
    api_key = os.getenv("BINANCE_API_KEY")
    secret = os.getenv("BINANCE_SECRET")
    
    if not api_key or not secret:
        print("[!] ERROR: Binance credentials not found.")
        return

    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': secret,
        'enableRateLimit': True,
        'options': {'defaultType': 'margin'}
    })

    try:
        print("--- BINANCE MARGIN WALLET AUDIT (V300) ---")
        balance = exchange.fetch_balance()
        
        # 1. High Level Summary
        info = balance['info']
        total_equity = float(info.get('totalMarginEquity', 0))
        total_debt = float(info.get('totalLiabilityOfBtc', 0)) # BTC denom, but gives idea
        margin_level = float(info.get('marginLevel', 999.0))
        
        print(f"\n[SUMMARY]")
        print(f"Total Net Equity: ${total_equity:.2f} USDT")
        print(f"Margin Level (Risk): {margin_level:.2f}")
        print(f"Account Status: {'HEALTHY' if margin_level > 2.0 else 'WARNING' if margin_level > 1.5 else 'DANGER'}")

        # 2. Asset Breakdown
        print(f"\n[ASSET BREAKDOWN]")
        user_assets = info.get('userAssets', [])
        for asset in user_assets:
            a_name = asset['asset']
            free = float(asset['free'])
            borrowed = float(asset['borrowed'])
            interest = float(asset['interest'])
            locked = float(asset['locked'])
            
            if free > 0 or borrowed > 0 or locked > 0:
                print(f"- {a_name:6}: Free: {free:12.4f} | Borrowed: {borrowed:12.4f} | Debt: {interest:12.4f}")

        # 3. Market Opportunity
        print(f"\n[MARKET CAPACITY]")
        # Binance Margin typically allows 3x to 5x leverage on USDT
        buying_power = total_equity * 3.0 # Conservative power
        print(f"Max Safe Buying Power: ~${buying_power:.2f} USDT")
        
    except Exception as e:
        print(f"[!] AUDIT ERROR: {e}")

if __name__ == "__main__":
    audit_wallet()
