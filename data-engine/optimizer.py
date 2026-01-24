import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env.local")

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Optimizer: Supabase credentials missing.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_recent_performance(limit=20):
    """Fetches last N closed trades to analyze performance."""
    try:
        res = supabase.table("paper_positions") \
            .select("*") \
            .eq("status", "CLOSED") \
            .order("closed_at", desc=True) \
            .limit(limit) \
            .execute()
        return res.data
    except Exception as e:
        print(f"Optimizer Fetch Error: {e}")
        return []

def update_params(updates):
    """Updates the active bot parameters."""
    try:
        # Assuming single active row logic for now
        supabase.table("bot_params") \
            .update(updates) \
            .eq("active", "true") \
            .execute()
        print(f"   >>> V6 OPTIMIZER: Parameters Updated: {updates}")
        
        # Log action
        supabase.table("error_logs").insert({
            "service": "OPTIMIZER",
            "error_level": "INFO",
            "message": f"Strategy Adapted: {updates}"
        }).execute()
        
    except Exception as e:
        print(f"Optimizer Update Error: {e}")

def run_optimization():
    print("--- RUNNING V6 SELF-OPTIMIZATION ---")
    history = get_recent_performance(20)
    
    if not history or len(history) < 5:
        print("   >>> Not enough data to optimize (Need > 5 trades).")
        return

    # 1. Calculate Metrics
    wins = len([t for t in history if (t.get('pnl') or 0) > 0])
    total = len(history)
    win_rate = (wins / total) * 100
    
    # Calculate Avg ROE
    roes = []
    for t in history:
        margin = t.get('initial_margin') or ((t.get('entry_price') * abs(t.get('quantity'))) / 10) # Fallback 10x
        if margin > 0:
            roe = (t.get('pnl') or 0) / margin
            roes.append(roe)
    
    avg_roe = (sum(roes) / len(roes)) * 100 if roes else 0
    
    print(f"   >>> ANALYSIS: Win Rate: {win_rate:.1f}% | Avg ROE: {avg_roe:.1f}%")
    
    # 2. Get Current Params to Modify
    current_params = supabase.table("bot_params").select("*").eq("active", "true").limit(1).execute().data[0]
    
    current_lev = current_params.get('default_leverage', 10)
    current_rsi = current_params.get('rsi_buy_threshold', 30)
    
    updates = {}
    
    # 3. ADAPTATION LOGIC
    
    # SCENARIO A: PERFORMANCE IS BAD (Win Rate < 35%)
    # Action: Defensive Mode. Lower Leverage, Stricter Entry.
    if win_rate < 35:
        print("   !!! PERFORMANCE ALERT: Enabling Defensive Mode.")
        if current_lev > 5:
            updates['default_leverage'] = max(2, current_lev - 2) # Reduce Leverage
        
        if current_rsi > 20:
            updates['rsi_buy_threshold'] = max(20, current_rsi - 5) # Tighten Entry (Only buy extreme dips)
            
        updates['stop_loss_atr_mult'] = 2.0 # Widen Stops to avoid chop
            
    # SCENARIO B: PERFORMANCE IS GOOD (Win Rate > 60%)
    # Action: Aggressive Mode. Increase Leverage.
    elif win_rate > 60:
         print("   $$$ PERFORMANCE EXCELLENT: Scaling Up.")
         if current_lev < 50:
             updates['default_leverage'] = min(50, current_lev + 2) # Increase Leverage
             
         if current_rsi < 40:
             updates['rsi_buy_threshold'] = min(40, current_rsi + 2) # Loosen Entry (Buy more often)

    # SCENARIO C: STABILIZATION (Neutral)
    else:
        # Slowly revert to defaults if things are average
        if current_lev != 10:
            # Gravitate towards 10
            updates['default_leverage'] = 10 if abs(current_lev - 10) < 2 else (current_lev - 1 if current_lev > 10 else current_lev + 1)
            
    if updates:
        update_params(updates)
    else:
        print("   >>> No Optimization needed. Strategy stable.")

if __name__ == "__main__":
    run_optimization()
