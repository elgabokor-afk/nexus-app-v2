
import os
import time
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# V3300: Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

url: str = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("❌ Error: Missing Supabase credentials")
    exit(1)

supabase: Client = create_client(url, key)

def wipe_table(table_name):
    try:
        print(f"🧹 Wiping table: {table_name}...")
        # Delete all rows (neq filtering on id avoids 'delete all' restriction in some client libs, 
        # but pure postgrest usually encourages explicit filters. 
        # Using a dummy filter 'id.neq.0' is a common trick if 'delete()' requires a filter.)
        # However, supabase-py delete usually works if RLS allows or Service Key used.
        # We will try standard delete.
        res = supabase.table(table_name).delete().neq("id", 0).execute()
        print(f"   ✅ Deleted {len(res.data) if res.data else 0} rows from {table_name}")
    except Exception as e:
        # V3300: Ignore 'Table not found' (404/PGRST205)
        if "404" in str(e) or "Relation" in str(e) or "PGRST205" in str(e):
             print(f"   ⚠️ Table {table_name} not found or empty (skipping).")
        else:
             print(f"   ❌ Error wiping {table_name}: {e}")

def unlink_closed_trades():
    """
    V3300: Unlink closed trades from signals to prevent FK violations.
    """
    try:
        print("🔗 Unlinking closed trades from signals...")
        # Update paper_wallet where status=CLOSED set signal_id=NULL
        # Note: supabase-py update syntax
        res = supabase.table("paper_wallet").update({"signal_id": None}).eq("status", "CLOSED").execute()
        print(f"   ✅ Unlinked {len(res.data) if res.data else 0} closed trades.")
    except Exception as e:
        print(f"   ⚠️ Error unlinking trades: {e}")

def main():
    print("🚀 Starting V3300 Smart Database Purge...")
    
    # 1. Unlink FK dependencies
    unlink_closed_trades()
    
    # 2. Wipe high-volume tables
    tables = ["market_signals", "market_events", "order_book_snapshots", "ai_inferences"]
    
    for t in tables:
        wipe_table(t)
        time.sleep(0.5)
        
    print("✨ Database cleanup complete!")

if __name__ == "__main__":
    main()
