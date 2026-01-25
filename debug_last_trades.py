import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")

url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("--- DEBUGGING RECENT TRADES ---")
res = supabase.table("paper_positions").select("*").order("opened_at", desc=True).limit(10).execute()

for t in res.data:
    symbol = t['symbol']
    side = t['signal_type']
    entry = float(t['entry_price'])
    tp = float(t['bot_take_profit'] or 0)
    sl = float(t['bot_stop_loss'] or 0)
    
    status = "VALID"
    if "BUY" in side:
        if tp <= entry: status = "INVALID (TP <= Entry on BUY)"
    elif "SELL" in side:
        if tp >= entry: status = "INVALID (TP >= Entry on SELL)"
        
    print(f"ID: {t['id']} | {symbol} | {side} | Entry: {entry} | TP: {tp} | SL: {sl} -> {status}")
