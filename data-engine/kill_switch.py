import os
import ccxt
from dotenv import load_dotenv

# Load credentials
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

def kill_everything():
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
        print("--- BINANCE MARGIN KILL SWITCH ACTIVATED ---")
        
        # 1. Cancel all open orders
        print("   >>> Cancelling all open margin orders...")
        # Since we are in margin, we need to iterate or use specific endpoints
        # exchange.cancel_all_orders() works if supported by the exchange
        # For Binance Margin, we might need to specify symbols or iterate
        
        # Get all open orders
        open_orders = exchange.fetch_open_orders()
        if not open_orders:
            print("   [OK] No open orders found.")
        else:
            for order in open_orders:
                print(f"   [CANCEL] ID: {order['id']} | {order['symbol']} | {order['side']}")
                exchange.cancel_order(order['id'], order['symbol'])
            print(f"   [SUCCESS] Cancelled {len(open_orders)} orders.")

        # 2. Monitor Positions
        print("\n   --- ACTIVE POSITIONS ---")
        balance = exchange.fetch_balance({'type': 'margin'})
        found = False
        for asset, total in balance['total'].items():
            if total > 0 and asset != 'USDT':
                print(f"   [ALERT] Active Position: {asset} (Total: {total})")
                print(f"   [NOTICE] Please close positions manually in Binance UI to ensure safe deleveraging.")
                found = True
        
        if not found:
            print("   [OK] No active debt/positions found.")

        print("\n--- EMERGENCY STOP COMPLETE ---")
        
    except Exception as e:
        print(f"[!] KILL SWITCH ERROR: {e}")

if __name__ == "__main__":
    kill_everything()
