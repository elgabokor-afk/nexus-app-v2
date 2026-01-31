
import os
import time
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Load Env Robustly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
env_path = os.path.join(parent_dir, '.env.local')

if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded config from: {env_path}")
else:
    print(f"Warning: .env.local not found at {env_path}")

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print("--- ORACLE SYSTEM HEALTH CHECK ---")
print(f"Target: {SUPABASE_URL}")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("!!! CRITICAL: Missing Supabase Credentials in .env.local")
    exit(1)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. Latency Test (Read)
    start = time.time()
    res = supabase.table("profiles").select("count", count="exact").limit(1).execute()
    latency = (time.time() - start) * 1000
    print(f"1. [LATENCY] Read Ping: {latency:.2f}ms")
    
    if latency > 500:
        print("   [WARN] High Latency detected (>500ms). Real-time feel may be degraded.")
    else:
        print("   [OK] Connection Speed is Good.")

    # 2. Schema Integrity Check
    tables = ["signals", "paper_positions", "paper_trades", "bot_wallet"]
    for table in tables:
        try:
            # Try to fetch 1 row to see if table exists and permissions work
            res = supabase.table(table).select("*").limit(1).execute()
            print(f"2. [SCHEMA] Table '{table}': OK (Accessible)")
        except Exception as e:
            print(f"   [CRITICAL] Table '{table}' Check Failed: {e}")

    # 3. Data Freshness (Signals)
    res = supabase.table("signals").select("created_at").order("created_at", desc=True).limit(1).execute()
    if res.data:
        last_sig = res.data[0]['created_at']
        print(f"3. [FRESHNESS] Last Signal: {last_sig}")
        # Parse and check if recent (logic omitted for brevity, just showing user)
    else:
        print("3. [FRESHNESS] No Signals found in DB.")

    # 4. Data Freshness (Positions)
    res = supabase.table("paper_positions").select("closed_at").order("closed_at", desc=True).limit(1).execute()
    if res.data:
        last_pos = res.data[0]['closed_at']
        print(f"4. [FRESHNESS] Last Position Activity: {last_pos}")
    
    # 5. Check 'symbol' column fix
    try:
        # We try to select 'symbol' specifically. If it fails, schema is wrong.
        res = supabase.table("signals").select("symbol").limit(1).execute()
        print("5. [INTEGRITY] 'symbol' column check: OK (Migration Applied)")
    except Exception as e:
        print("   [CRITICAL] 'symbol' column MISSING. Run fix_signal_schema.sql immediately.")

    print("\n--- DIAGNOSTIC COMPLETE ---")

except Exception as e:
    print(f"\n!!! SYSTEM ERROR: {e}")
