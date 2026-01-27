import os
import asyncio
from supabase import create_client, Client

# User Provided Credentials (verified against .env.local)
url = "https://uxjjqrctxfajzicruvxc.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4ampxcmN0eGZhanppY3J1dnhjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkwMjM1NjYsImV4cCI6MjA4NDU5OTU2Nn0.MyzhM7h5xM45SwtZ40DoaS_Cg6SMByuYVrBkmIhNYPM"

supabase: Client = create_client(url, key)

async def check():
    print("--- DIAGNOSTIC START ---")
    try:
        # 1. Count Signals
        response = supabase.table("signals").select("*", count="exact").limit(1).execute()
        count = response.count
        print(f"Signals Count: {count}")
        
        if count == 0:
            print("WARNING: Table 'signals' is empty.")
        else:
            print("SUCCESS: Data exists.")
            # Print latest signal
            latest = response.data[0]
            print(f"Latest Signal: {latest.get('pair')} | {latest.get('created_at')}")

        # 2. Check VIP Table (if accessible)
        try:
            vip_res = supabase.table("vip_signal_details").select("*", count="exact").limit(1).execute()
            print(f"VIP Signals Count: {vip_res.count}")
        except Exception as e:
            print(f"VIP Check Failed (Expected if Anon): {e}")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
    print("--- DIAGNOSTIC END ---")

if __name__ == "__main__":
    asyncio.run(check())
