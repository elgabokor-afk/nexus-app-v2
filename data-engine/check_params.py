import os
import json
from supabase import create_client
from dotenv import load_dotenv

# Load Env
load_dotenv(dotenv_path='.env.local')

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_params():
    print("--- CHECKING BOT PARAMS ---")
    try:
        res = supabase.table("bot_params").select("*").eq("active", "true").limit(1).execute()
        if res.data:
            print("Active Params Found:")
            print(json.dumps(res.data[0], indent=2))
        else:
            print("No active params found. Using Code Defaults.")
    except Exception as e:
        print(f"Error fetching params: {e}")

if __name__ == "__main__":
    check_params()
