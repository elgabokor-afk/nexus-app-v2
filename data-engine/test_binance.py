import os
import ccxt
from dotenv import load_dotenv

# Load credentials
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
env_path = os.path.join(parent_dir, '.env.local')
load_dotenv(dotenv_path=env_path)

def test_binance_connection():
    api_key = os.getenv("BINANCE_API_KEY")
    secret = os.getenv("BINANCE_SECRET")
    
    print(f"Testing Binance connection with API Key: {api_key[:5]}...{api_key[-5:]}")
    
    try:
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
        time_diff = exchange.load_time_difference()
        print(f"--- Time Logic: Local Clock is {time_diff}ms diff from Server ---")
        
        balance = exchange.fetch_balance()
        usdt_free = balance['total'].get('USDT', 0)
        print("--- CONNECTION SUCCESSFUL! ---")
        print(f"--- Current Binance Futures USDT Balance: ${usdt_free:.2f} ---")
        
    except Exception as e:
        print(f"--- CONNECTION FAILED: {e} ---")

if __name__ == "__main__":
    test_binance_connection()
