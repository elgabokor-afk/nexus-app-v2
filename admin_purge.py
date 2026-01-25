import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load Env (Service Role Key is vital here)
load_dotenv(dotenv_path=".env.local")

URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not URL or not KEY:
    print("❌ Critical: Supabase Secrets missing in .env.local")
    exit()

print("--- 🧹 NEXUS ADMIN PURGE (V3200) ---")
print("Authenticating with SERVICE_ROLE_KEY (God Mode)...")
supabase = create_client(URL, KEY)

# 0. Unlink Closed Trades (Fix FK Constraint)
# We remove the link to signals for CLOSED trades so we can delete the signal data.
print("\n[Optimization] Unlinking signals from CLOSED trades...")
try:
    # Update explicitly closed positions to have NULL signal_id
    # Note: We do this locally or via specific filter if volume is high, but simple update works for now.
    res = supabase.table("paper_positions") \
        .update({"signal_id": None}) \
        .eq("status", "CLOSED") \
        .neq("signal_id", None) \
        .execute()
    print(f"   ✅ Unlinked closed trades.")
except Exception as e:
    print(f"   ⚠️ Unlink Info: {e}")

def purge_table(table_name, column, hours_retention):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours_retention)).isoformat()
    print(f"\n[Cleaning '{table_name}'] Keeping last {hours_retention} hours...")
    
    try:
        res = supabase.table(table_name) \
            .delete() \
            .lt(column, cutoff) \
            .execute()
        print(f"   ✅ Cleaned outdated rows.")
    except Exception as e:
        # Ignore "Table not found" errors (PGRST205) as they mean 0 usage.
        if "PGRST205" in str(e):
             print(f"   ℹ️ Table not found (Empty). Skipping.")
        else:
             print(f"   ⚠️ Error: {e}")

# 1. High Velocity Tables (Delete everything > 6 hours old)

# 1. High Velocity Tables (Delete everything > 6 hours old)
# Measurements/Signals are only useful for immediate trading.
purge_table("market_signals", "timestamp", 6)
purge_table("analytics_signals", "created_at", 6)
purge_table("oracle_insights", "created_at", 6)

# 2. Logs (Keep 24h for debugging)
purge_table("error_logs", "created_at", 24)

# 3. Brain Memory (DO NOT DELETE)
print("\n[Skipping 'ai_model_registry'] -> Preserving AI Long-Term Memory")
print("[Skipping 'paper_positions'] -> Preserving Trade History")

print("\n--- ✨ SPACE RECLAIMED SUCCESSFULLY ---")
print("Your Supabase database is now optimized.")
