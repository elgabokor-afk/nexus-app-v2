import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")

url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("--- COSMOS BRAIN STATUS REPORT ---")

# 1. Valid Experience (Trades)
try:
    res = supabase.table("paper_positions") \
        .select("id", count="exact") \
        .eq("status", "CLOSED") \
        .neq("exit_reason", "FORCE_PURGE_V1500") \
        .neq("exit_reason", "ZOMBIE_AUTO_ARCHIVE") \
        .execute()
    valid_count = res.count
except:
    valid_count = 0

print(f"Experience: {valid_count} Valid Closed Trades")

# 2. Brain Metadata
try:
    res = supabase.table("ai_model_registry") \
        .select("*") \
        .order("last_bootstrap_at", desc=True) \
        .limit(1) \
        .execute()
        
    if res.data:
        brain = res.data[0]
        acc = float(brain.get('accuracy', 0)) * 100
        samples = brain.get('samples_trained', 0)
        version = brain.get('version_tag', 'v0')
        updated = brain.get('last_bootstrap_at')
        print(f"Version: {version}")
        print(f"Internal Accuracy: {acc:.1f}%")
        print(f"Samples Trained On: {samples}")
        print(f"Last Update: {updated}")
    else:
        print("Brain State: No training metadata found (New Brain).")

except Exception as e:
    print(f"Error fetching metadata: {e}")
