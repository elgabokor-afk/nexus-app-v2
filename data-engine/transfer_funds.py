import os
import ccxt
from dotenv import load_dotenv

# Load credentials
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
env_path = os.path.join(parent_dir, '.env.local')
load_dotenv(dotenv_path=env_path)

def transfer_all_funds():
    api_key = os.getenv("BINANCE_API_KEY")
    secret = os.getenv("BINANCE_SECRET")
    
    print("--- CONNECTING TO BINANCE ---")
    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': secret,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',
            'adjustForTimeDifference': True,
            'recvWindow': 10000
        }
    })
    
    # Manually trigger time sync
    exchange.load_time_difference()

    try:
        # 1. Transfer from MARGIN (Cross) to SPOT
        # Check Margin Balance
        try:
            margin_balance = exchange.fetch_balance({'type': 'margin'})
            usdt_margin = margin_balance['total'].get('USDT', 0)
            print(f"[MARGIN] Cross Margin USDT: ${usdt_margin:.2f}")
            
            if usdt_margin > 1:
                print(f"   >> Transferring ${usdt_margin:.2f} from Margin -> Spot...")
                # code: USDT, amount, fromAccount, toAccount
                exchange.transfer('USDT', usdt_margin, 'margin', 'spot')
                print("   [OK] Transfer Complete.")
            else:
                print("   >> No significant funds in Margin.")
        except Exception as e:
            print(f"   [WARN] Could not check/transfer Margin: {e}")

        # 2. Transfer from SPOT to FUTURES
        spot_balance = exchange.fetch_balance({'type': 'spot'})
        usdt_spot = spot_balance['total'].get('USDT', 0)
        print(f"[SPOT] Spot Account USDT: ${usdt_spot:.2f}")
        
        if usdt_spot > 1:
            print(f"   >> Transferring ${usdt_spot:.2f} from Spot -> Futures...")
            exchange.transfer('USDT', usdt_spot, 'spot', 'future')
            print("   [OK] Transfer Complete.")
        else:
            print("   >> No significant funds in Spot.")
            
        # 3. Final Check
        futures_balance = exchange.fetch_balance({'type': 'future'})
        usdt_futures = futures_balance['total'].get('USDT', 0)
        print(f"\n[FUTURES] FINAL BALANCE: ${usdt_futures:.2f}")
        print("   Ready to trade!")
        
    except Exception as e:
        print(f"[ERROR] Error during transfer: {e}")

if __name__ == "__main__":
    transfer_all_funds()
