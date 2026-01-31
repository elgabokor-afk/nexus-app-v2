import requests
import json

def get_top_vol_oracle(limit=20):
    try:
        print("Attempting to fetch Binance Ticker Data...")
        url = "https://api.binance.com/api/v3/ticker/24hr"
        res = requests.get(url, timeout=10)
        print(f"Status Code: {res.status_code}")
        
        data = res.json()
        print(f"Total Tickers Found: {len(data)}")
        
        # Filter USDT
        usdt_pairs = [
            t for t in data 
            if t['symbol'].endswith('USDT') 
            and 'UP' not in t['symbol'] 
            and 'DOWN' not in t['symbol']
        ]
        
        print(f"USDT Pairs Found: {len(usdt_pairs)}")
        
        # Sort by Quote Volume
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
        
        top_symbols = []
        for p in sorted_pairs[:limit]:
            sym = p['symbol']
            formatted = f"{sym[:-4]}/{sym[-4:]}"
            top_symbols.append(formatted)
            
        print(f"Top {limit} Assets: {top_symbols}")
        return top_symbols
    except Exception as e:
        print(f"!!! Error: {e}")
        return []

if __name__ == "__main__":
    get_top_vol_oracle()
