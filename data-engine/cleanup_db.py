import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load env from parent dir
load_dotenv('.env.local')

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing Supabase credentials in .env.local")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def cleanup():
    print("--- EMERGENCY DATABASE CLEANUP ---")
    
    # 1. Count open trades
    res = supabase.table("paper_positions").select("id", count="exact").eq("status", "OPEN").execute()
    count = res.count or 0
    print(f"Found {count} positions marked as OPEN.")
    
    if count == 0:
        print("Database is already clean. No action needed.")
        return

    # 2. Force Close
    print(f"Closing {count} positions... please wait.")
    try:
        supabase.table("paper_positions") \
            .update({"status": "CLOSED", "exit_reason": "ZOMBIE_PURGE"}) \
            .eq("status", "OPEN") \
            .execute()
        print("[SUCCESS] All zombie positions have been closed.")
        print("You can now restart paper_trader.py")
    except Exception as e:
        print(f"[ERROR] Failed to clean database: {e}")

if __name__ == "__main__":
    cleanup()
