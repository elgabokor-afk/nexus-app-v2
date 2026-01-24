import os
import pandas as pd
import numpy as np
from supabase import create_client, Client
from dotenv import load_dotenv

# Safe Import for ML Libraries
try:
    import joblib
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.impute import SimpleImputer
    ML_AVAILABLE = True
except ImportError as e:
    print(f"!!! Cosmos Engine Warning: ML libraries not found ({e}). Running in SAFE MODE.")
    ML_AVAILABLE = False

load_dotenv(dotenv_path="../.env.local")

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
MODEL_PATH = "cosmos_model.joblib"

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Cosmos Engine: Supabase credentials missing (Check .env.local)") 

class CosmosBrain:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.model = None
        
        if ML_AVAILABLE:
            self.imputer = SimpleImputer(strategy='mean')
        else:
            self.imputer = None
            
        self.feature_cols = ['rsi_value', 'imbalance_ratio', 'spread_pct', 'atr_value', 'macd_line', 'histogram']
        self.is_trained = False
        self.load_model()

    def load_model(self):
        if not ML_AVAILABLE: return
        
        if os.path.exists(MODEL_PATH):
            try:
                data = joblib.load(MODEL_PATH)
                self.model = data['model']
                self.imputer = data['imputer']
                self.is_trained = True
                print("   >>> Cosmos Brain: Loaded existing neural pathways.")
            except Exception as e:
                print(f"   >>> Cosmos Brain: Load failed ({e}). Starting fresh.")
    
    def save_model(self):
        if not ML_AVAILABLE or not self.model: return
        try:
            joblib.dump({'model': self.model, 'imputer': self.imputer}, MODEL_PATH)
            print("   >>> Cosmos Brain: Knowledge saved to disk.")
        except Exception as e:
            print(f"   >>> Cosmos Brain: Save failed ({e})")

    def fetch_training_data(self):
        """Fetches Closed Trades + Analytics Signals for training."""
        try:
            # 1. Get Closed Trades
            res_pos = self.supabase.table("paper_positions") \
                .select("signal_id, pnl, status") \
                .eq("status", "CLOSED") \
                .not_.is_("signal_id", "null") \
                .limit(500) \
                .execute()
            
            positions = res_pos.data
            if not positions: return pd.DataFrame()
            
            # 2. Extract Signal IDs
            sig_ids = [p['signal_id'] for p in positions]
            
            # 3. Get Analytics for these signals
            # Note: In production with thousands of signals, this batch fetch needs pagination or join.
            # optimized for V8 MVP (<500 items).
            res_analytics = self.supabase.table("analytics_signals") \
                .select("*") \
                .in_("signal_id", sig_ids) \
                .execute()
            
            analytics = res_analytics.data
            if not analytics: return pd.DataFrame()
            
            # 4. Merge
            df_pos = pd.DataFrame(positions)
            df_ana = pd.DataFrame(analytics)
            
            # Join on signal_id
            df = pd.merge(df_pos, df_ana, on='signal_id', how='inner')
            
            # 5. Define Target: 1 if PnL > 0, else 0
            df['target'] = (df['pnl'] > 0).astype(int)
            
            return df
        except Exception as e:
            print(f"   !!! Cosmos Data Fetch Error: {e}")
            return pd.DataFrame()

    def train(self):
        if not ML_AVAILABLE:
            print("   >>> Cosmos Brain: Training skipped (Safe Mode).")
            return

        print("   >>> Cosmos Brain: Entering Deep Sleep Training Mode...")
        df = self.fetch_training_data()
        
        if df.empty or len(df) < 10:
            print("   >>> Cosmos Brain: Not enough data to train (Need > 10 trades).")
            return
            
        X = df[self.feature_cols]
        y = df['target']
        
        # Handle missing values (e.g. old signals without MACD)
        X = pd.DataFrame(self.imputer.fit_transform(X), columns=self.feature_cols)
        
        # Train Random Forest
        # n_estimators=100 (100 Decision Trees)
        self.model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        self.model.fit(X, y)
        
        accuracy = self.model.score(X, y) # Training accuracy (overfit proxy but ok for self-check)
        self.is_trained = True
        self.save_model()
        
        print(f"   >>> Cosmos Brain: Training Complete. Accuracy on Memory: {accuracy:.2%}")

    def get_trend_status(self, features):
        """Simple trend classifier based on EMA/Price."""
        price = features.get('price', 0)
        ema = features.get('ema_200', price)
        if price > ema: return "BULLISH"
        if price < ema: return "BEARISH"
        return "NEUTRAL"

    def generate_reasoning(self, features, prob):
        """
        V40: The BLM (Bot Language Model) reasoning layer.
        Converts technical data into high-level strategic thoughts.
        """
        rsi = features.get('rsi_value', 50)
        imb = features.get('imbalance_ratio', 0)
        macd_h = features.get('histogram', 0)
        trend = self.get_trend_status(features)
        
        insights = []
        
        # 1. Trend Awareness
        if trend == "BULLISH":
            insights.append("Price is holding above the EMA_200, confirming a primary bullish structure.")
        elif trend == "BEARISH":
            insights.append("Price is trading below the EMA_200; descending pressure is dominant.")
            
        # 2. RSI Exhaustion
        if rsi < 30:
            insights.append("RSI is oversold, indicating high potential for a mean-reversion bounce.")
        elif rsi > 70:
            insights.append("RSI is overbought; buy pressure may be exhausted.")
            
        # 3. Market Depth/Flow
        if imb > 0.4:
            insights.append(f"Heavy buy-side order book imbalance ({imb*100:.1f}%) detected.")
        elif imb < -0.4:
            insights.append(f"Strong sell-side pressure ({abs(imb)*100:.1f}%) in the local order book.")
            
        # 4. Momentum
        if macd_h > 0:
            insights.append("MACD histogram is positive, showing growing bullish momentum.")
        elif macd_h < 0:
            insights.append("Momentum is decelerating as indicated by the negative MACD histogram.")

        # Final Synthesis
        conviction = "Neutral"
        if prob > 0.7: conviction = "High Conviction"
        elif prob > 0.6: conviction = "Moderate Conviction"
        elif prob < 0.4: conviction = "High Risk / Bearish Trap"
        
        summary = " ".join(insights)
        return f"{conviction}: {summary}"

    def predict_success(self, features):
        """
        Predicts probability of WIN.
        features: dict with keys matching feature_cols
        """
        if not ML_AVAILABLE:
            return 0.5 # Neutral Safe Mode

        if not self.is_trained:
            return 0.5 # Neutral if untrained
            
        try:
            # Convert dict to DF
            input_df = pd.DataFrame([features])
            
            # Fill missing columns if any
            for col in self.feature_cols:
                if col not in input_df.columns:
                    input_df[col] = 0
            
            # Reorder
            input_df = input_df[self.feature_cols]
            
            # Impute
            input_data = self.imputer.transform(input_df)
            
            # Predict Prob of Class 1 (Win)
            prob = self.model.predict_proba(input_data)[0][1]
            return prob
        except Exception as e:
            print(f"Prediction Error: {e}")
            return 0.5

    def decide_trade(self, signal_type, features, oracle_insight=None):
        """
        V45/V50: The Master AI Decision Engine.
        Returns (Bool: Should Trade, Float: Final Prob, String: Reason)
        """
        prob = self.predict_success(features)
        trend = self.get_trend_status(features)
        
        # 1. BASELINE: Apply user-requested 90% confidence from params
        base_decision = prob >= 0.90
        
        # 2. ORDER BOOK SENSITIVITY (Strong changes)
        imb = features.get('imbalance_ratio', 0)
        strong_imbalance_buy = (signal_type == "BUY" and imb > 0.65)
        strong_imbalance_sell = (signal_type == "SELL" and imb < -0.65)
        
        if strong_imbalance_buy or strong_imbalance_sell:
            prob += 0.05 # +5% boost for strong book support
            
        # 3. TREND ALIGNMENT (Strict)
        trend_aligned = (signal_type == "BUY" and trend == "BULLISH") or \
                        (signal_type == "SELL" and trend == "BEARISH")
                        
        if not trend_aligned:
            if prob < 0.95:
                reason = f"Decision REJECTED: Trend ({trend}) does not align with {signal_type} signal. AI requires 95%+, got {prob*100:.1f}%."
                return False, prob, reason

        # 4. V50: ORACLE CONFLUENCE (The Gateway)
        # Check if the 1m Oracle insight matches the 1h Signal direction
        if oracle_insight:
            o_trend = oracle_insight.get('trend_status')
            o_reasoning = oracle_insight.get('reasoning', '')
            
            oracle_aligned = (signal_type == "BUY" and o_trend == "BULLISH") or \
                             (signal_type == "SELL" and o_trend == "BEARISH")
            
            if not oracle_aligned:
                # Oracle is screaming Mismatch (e.g. 1m chart is crashing while 1h signal says buy)
                reason = f"Decision REJECTED: Oracle (1m) is {o_trend} while Signal is {signal_type}. Confluence Failed. Reasoning: {o_reasoning}"
                return False, prob, reason
            
            print(f"       [ORACLE CONFIRMED] 1m Analysis aligns with {signal_type} signal.")

        # 5. FINAL WEIGHTED DECISION
        required_prob = 0.90
        if trend_aligned and (abs(imb) > 0.4):
            required_prob = 0.85 # AI is more lenient if confluence is perfect
            
        should_trade = prob >= required_prob
        
        reasoning = self.generate_reasoning(features, prob)
        final_reason = f"AI {'DECIDED TO TRADE' if should_trade else 'REJECTED'}: Confidence: {prob*100:.1f}%. Target: {required_prob*100:.1f}%. Context: {reasoning}"
        
        return should_trade, prob, final_reason

# Singleton Instance for easy import
brain = CosmosBrain()

if __name__ == "__main__":
    # Manual Training Trigger
    brain.train()
