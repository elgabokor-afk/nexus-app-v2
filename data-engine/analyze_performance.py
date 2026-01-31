import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
from dotenv import load_dotenv

# Load env variables
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
env_path = os.path.join(parent_dir, '.env.local')
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def analyze_losses():
    print("--- COSMOS FORENSIC ANALYSIS (V120) ---")
    
    # Fetch last 50 closed trades
    try:
        response = supabase.table("paper_positions") \
            .select("*") \
            .eq("status", "CLOSED") \
            .order("closed_at", desc=True) \
            .limit(50) \
            .execute()
            
        trades = response.data
        if not trades:
            print("No closed trades found to analyze.")
            return

        df = pd.DataFrame(trades)
        print(f"DEBUG: Available Columns: {list(df.columns)}")
        
        # Calculate Metrics
        total_trades = len(df)
        wins = df[df['pnl'] > 0]
        losses = df[df['pnl'] <= 0]
        win_rate = (len(wins) / total_trades) * 100
        
        total_pnl = df['pnl'].sum()
        avg_loss = losses['pnl'].mean() if not losses.empty else 0
        avg_win = wins['pnl'].mean() if not wins.empty else 0
        
        print(f"\nPERFORMANCE SUMMARY (Last {total_trades} trades)")
        print(f"   Win Rate:      {win_rate:.2f}%")
        print(f"   Total PnL:     ${total_pnl:.2f}")
        print(f"   Avg Win:       ${avg_win:.2f}")
        print(f"   Avg Loss:      ${avg_loss:.2f}")
        
        # Diagnosis: Why are we losing?
        print("\nLOSS ANATOMY (Recent 10 Losses)")
        print(f"{'Symbol':<10} {'Dir':<6} {'Entry':<10} {'Exit':<10} {'PnL':<10} {'Type':<6} {'Reason'}")
        print("-" * 70)
        
        for _, trade in losses.head(10).iterrows():
            signal_type = str(trade.get('signal_type', ''))
            direction = "LONG" if "BUY" in signal_type else "SHORT" if "SELL" in signal_type else "UNKNOWN"
            
            trade_type = "LIQ" if "LIQ" in signal_type else "TECH"
            reason = trade.get('exit_reason', 'Unknown')
            
            entry = float(trade.get('entry_price', 0))
            exit_p = float(trade.get('exit_price', 0))
            pnl = float(trade.get('pnl', 0))
            
            print(f"{trade['symbol']:<10} {direction:<6} ${entry:<9.4f} ${exit_p:<9.4f} ${pnl:<9.2f} {trade_type:<6} {reason}")
            
        # Recommendations
        print("\n🤖 COSMOS DIAGNOSIS:")
        if win_rate < 40:
            print("   ⚠️ CRITICAL: Winrate < 40%. Market is likely CHOPPY/RANGING.")
            print("   👉 RECOMMENDATION: Enable ADX Filter (Stop trading if ADX < 25).")
        if avg_loss < (avg_win * -1.5):
            print("   ⚠️ RISK: Stops are too wide vs Winners.")
            print("   👉 RECOMMENDATION: Tighten SL Multipliers.")

    except Exception as e:
        print(f"Error analyzing trades: {e}")

if __name__ == "__main__":
    analyze_losses()
