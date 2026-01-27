import os
import json
from supabase import create_client
from dotenv import load_dotenv
import time

# Load Env
load_dotenv(dotenv_path='.env.local')

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_activity():
    print("--- RECENT SYSTEM ACTIVITY ---")
    
    # 1. Signals
    print("\n[LATEST SIGNALS]")
    try:
        res = supabase.table("signals").select("id, symbol, created_at, ai_confidence").order("created_at", desc=True).limit(5).execute()
        for s in res.data:
            print(f"   ID {s['id']}: {s['symbol']} | {s['created_at']} | Conf: {s['ai_confidence']}")
    except Exception as e:
        print(f"Error fetching signals: {e}")

    # 2. Error Logs
    print("\n[LATEST ERROR LOGS]")
    try:
        # Fetch generic error logs
        res = supabase.table("error_logs").select("created_at, message").order("created_at", desc=True).limit(5).execute()
        if not res.data:
            print("   (No recent errors found)")
        for err in res.data:
            print(f"   {err['created_at']} | {err['message']}")
    except Exception as e:
        print(f"Error fetching logs: {e}")

if __name__ == "__main__":
    check_activity()
