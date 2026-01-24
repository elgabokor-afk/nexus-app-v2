import os
import joblib
import pandas as pd
import numpy as np
from supabase import create_client, Client
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from dotenv import load_dotenv

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
        self.imputer = SimpleImputer(strategy='mean')
        self.feature_cols = ['rsi_value', 'imbalance_ratio', 'spread_pct', 'atr_value', 'macd_line', 'histogram']
        self.is_trained = False
        self.load_model()

    def load_model(self):
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
        if self.model:
            joblib.dump({'model': self.model, 'imputer': self.imputer}, MODEL_PATH)
            print("   >>> Cosmos Brain: Knowledge saved to disk.")

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

    def predict_success(self, features):
        """
        Predicts probability of WIN.
        features: dict with keys matching feature_cols
        """
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

# Singleton Instance for easy import
brain = CosmosBrain()

if __name__ == "__main__":
    # Manual Training Trigger
    brain.train()
