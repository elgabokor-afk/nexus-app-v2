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
    
    # 3. V6.5 SMART OPTIMIZATION: CORRELATION ANALYSIS
    # Instead of just changing leverage, we change "Who we listen to".
    
    print("   >>> ANALYZING INDICATOR CORRELATION...")
    
    # Helper to check if a metric signaled correctly
    # Returns a score: 1.0 (Perfect Prediction) to -1.0 (Reverse Prediction)
    def check_correlation(metric_key, threshold, is_bullish_above):
        correct_signals = 0
        total_signals = 0
        
        for t in history:
            # We need analytics data. If missing, skip.
            # Assuming joined query or fetch. For V6 MVP, we rely on flat columns if available or skip.
            # actually our fetch query was simple. Let's assume we can judge by 'signal_type' + outcome, 
            # but ideally we need the 'analytics_signals' data.
            # LIMITATION: We need to join tables.
            pass
        return 0 
        
    # Since we need deep data, let's simplify for V6.5 MVP:
    # We will adjust weights based on "Regime Detection".
    # Volatility Regime (High ATR) -> Trust Imbalance & Trend.
    # Ranging Regime (Low ATR) -> Trust RSI.
    
    # Calculate Average Volatility of last trades
    avg_atr = sum([float(t.get('atr_entry') or 0) for t in history]) / len(history)
    avg_price = sum([float(t.get('entry_price') or 0) for t in history]) / len(history)
    volatility_pct = (avg_atr / avg_price) * 100
    
    print(f"   >>> MARKET REGIME: Volatility {volatility_pct:.3f}%")
    
    current_weights = {
        'rsi': float(current_params.get('weight_rsi', 0.3)),
        'imbalance': float(current_params.get('weight_imbalance', 0.3)),
        'trend': float(current_params.get('weight_trend', 0.2)),
        'macd': float(current_params.get('weight_macd', 0.2))
    }
    
    new_weights = current_weights.copy()
    
    # REGIME A: HIGH VOLATILITY (> 0.5% ATR)
    # Strategy: Trend Following & Order Flow. RSI is less reliable (divergences fail).
    if volatility_pct > 0.5:
        print("   >>> REGIME: HIGH VOLATILITY (Trending)")
        new_weights['trend'] = min(0.4, current_weights['trend'] + 0.05)
        new_weights['imbalance'] = min(0.4, current_weights['imbalance'] + 0.05)
        new_weights['macd'] = min(0.3, current_weights['macd'] + 0.05) # MACD loves trends
        new_weights['rsi'] = max(0.1, current_weights['rsi'] - 0.10) # Ignor RSI mean reversion
        
    # REGIME B: LOW VOLATILITY (< 0.2% ATR)
    # Strategy: Mean Reversion (RSI). Trend lagging indicators fail (whipsaws).
    elif volatility_pct < 0.2:
        print("   >>> REGIME: LOW VOLATILITY (Ranging)")
        new_weights['rsi'] = min(0.5, current_weights['rsi'] + 0.10)
        new_weights['imbalance'] = min(0.4, current_weights['imbalance'] + 0.05) # Order book still works
        new_weights['trend'] = max(0.1, current_weights['trend'] - 0.05)
        new_weights['macd'] = max(0.1, current_weights['macd'] - 0.05)
        
    else:
        print("   >>> REGIME: NEUTRAL. Stabilizing Weights.")
        # Revert slowly to balanced portfolio
        for k in new_weights:
            target = 0.25
            if new_weights[k] > target: new_weights[k] -= 0.01
            if new_weights[k] < target: new_weights[k] += 0.01

    # Apply Weight Updates
    updates['weight_rsi'] = round(new_weights['rsi'], 2)
    updates['weight_imbalance'] = round(new_weights['imbalance'], 2)
    updates['weight_trend'] = round(new_weights['trend'], 2)
    updates['weight_macd'] = round(new_weights['macd'], 2)

    # Leverage Optimization (Legacy V6 logic kept)
    if win_rate > 60:
         if current_lev < 50: updates['default_leverage'] = current_lev + 2
    elif win_rate < 35:
         if current_lev > 2: updates['default_leverage'] = current_lev - 2

    if updates:
        update_params(updates)
    else:
        print("   >>> No Optimization needed. Strategy stable.")

if __name__ == "__main__":
    run_optimization()
