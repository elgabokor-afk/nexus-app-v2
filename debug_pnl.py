import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")

url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("--- DEBUGGING CLOSED TRADES ---")
res = supabase.table("paper_positions") \
    .select("symbol, pnl, exit_reason, closed_at") \
    .eq("status", "CLOSED") \
    .order("closed_at", desc=True) \
    .limit(20) \
    .execute()

for t in res.data:
    pnl = t['pnl']
    reason = t['exit_reason']
    symbol = t['symbol']
    print(f"Symbol: {symbol} | Reason: {reason} | PnL: {pnl}")
