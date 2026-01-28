import os
import pandas as pd
import numpy as np
from datetime import datetime, timezone
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

# Load env from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
MODEL_PATH = "cosmos_model.joblib"

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Cosmos Engine: Supabase credentials missing (Check .env.local)") 

from deep_brain import deep_brain # V490
from smc_engine import smc_engine # V560
from deepseek_engine import deepseek_engine # V700
from openai_engine import openai_engine # V800

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
        
        # V490: Link Deep Brain
        self.deep_brain = deep_brain

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
        """Fetches Closed Trades + Analytics Signals for training (V125: Includes Ghost Trades)."""
        try:
            # 1. Get Closed Trades (Select fallback features too)
            res_pos = self.supabase.table("paper_positions") \
                .select("signal_id, pnl, status, rsi_entry, atr_entry") \
                .eq("status", "CLOSED") \
                .limit(1000) \
                .execute()
            
            positions = res_pos.data
            if not positions: return pd.DataFrame()
            
            # 2. Extract Signal IDs (Filter out None, but keep 9999)
            sig_ids = [p['signal_id'] for p in positions if p['signal_id']]
            
            # 3. Get Analytics for these signals
            res_analytics = self.supabase.table("analytics_signals") \
                .select("*") \
                .in_("signal_id", sig_ids) \
                .execute()
            
            analytics = res_analytics.data
            df_pos = pd.DataFrame(positions)
            
            if not analytics:
                # If no analytics found (e.g. all manual trades), create empty DF with columns
                df_ana = pd.DataFrame(columns=['signal_id'] + self.feature_cols)
            else:
                df_ana = pd.DataFrame(analytics)
            
            # 4. Merge (Left Join to keep Ghost Trades)
            # V125: Use LEFT JOIN so manual/adopted trades aren't dropped
            df = pd.merge(df_pos, df_ana, on='signal_id', how='left')
            
            # 5. Feature Reconstruction (Fallback Logic)
            # If rsi_value is NaN (missing analytics), use rsi_entry from position
            if 'rsi_value' in df.columns and 'rsi_entry' in df.columns:
                df['rsi_value'] = df['rsi_value'].fillna(df['rsi_entry'])
                
            if 'atr_value' in df.columns and 'atr_entry' in df.columns:
                df['atr_value'] = df['atr_value'].fillna(df['atr_entry'])
            
            # Fill remaining missing technicals with Neutral/Zero
            df.fillna({
                'rsi_value': 50,
                'imbalance_ratio': 0, 
                'spread_pct': 0.0002, 
                'atr_value': 0, 
                'macd_line': 0, 
                'histogram': 0
            }, inplace=True)

            print(f"   [V125] Training Data Fetched: {len(df)} samples (Including recovered ghosts)")
            
            # 6. Define Target: 1 if PnL > 0, else 0
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
        
        # V72: Sync to Neural Link (Cloud)
        try:
            from db import sync_model_metadata
            sync_model_metadata(
                version=os.getenv("STRATEGY_VERSION", "1.0"),
                accuracy=accuracy,
                samples=len(df),
                features=self.feature_cols
            )
        except Exception as e:
            print(f"   !!! Neural Link Sync Failed: {e}")

    def get_trend_status(self, features):
        """Simple trend classifier based on EMA/Price."""
        price = features.get('price', 0)
        ema = features.get('ema_200', price)
        if price > ema: return "BULLISH"
        if price < ema: return "BEARISH"
        return "NEUTRAL"

    def validate_last_4h(self, symbol, df_5m):
        """
        V600: Dynamic Backtesting.
        Compares AI predictions on the last 4 hours of 5m candles with actual price movement.
        """
        if not self.is_trained or df_5m is None or len(df_5m) < 48: # 4h = 48 candles of 5m
             return 0.5 # Neutral if not enough data
             
        try:
            # Check last 12 predictions (approx last 1h of 'mood')
            correct_preds = 0
            test_samples = df_5m.tail(12) 
            
            for i in range(len(test_samples) - 1):
                row = test_samples.iloc[i]
                next_row = test_samples.iloc[i+1]
                
                # Mock features for this historical point
                feat = {
                    'rsi_value': row.get('rsi', 50),
                    'imbalance_ratio': 0, # Cannot backtest imbalance without historical book
                    'spread_pct': 0.0002,
                    'atr_value': row.get('atr', 0),
                    'macd_line': 0,
                    'histogram': 0
                }
                
                prob = self.predict_success(feat)
                real_gain = (next_row['close'] - row['close']) / row['close']
                
                # If AI was bullish (>0.5) and price went up, or bearish (<0.5) and price went down
                if (prob > 0.5 and real_gain > 0) or (prob < 0.5 and real_gain < 0):
                    correct_preds += 1
            
            recent_accuracy = correct_preds / 11
            print(f"       [BACKTEST] Recent 1h AI Accuracy for {symbol}: {recent_accuracy:.1%}")
            return recent_accuracy
        except Exception as e:
            print(f"   [BACKTEST ERROR] {e}")
            return 0.5

    def generate_reasoning(self, symbol, signal_type, features, prob):
        """
        V800: Master Reasoning Layer.
        Prioritizes OpenAI (GPT-4o), then DeepSeek, then Local BLM logic.
        """
        # 1. Primary: OpenAI (V800)
        # V1900: User requested OpenAI ONLY (DeepSeek deprecated due to balance)
        openai_reason = openai_engine.generate_trade_narrative(symbol, signal_type, features)
        if openai_reason:
            return f"[GPT-4o] {openai_reason}"

        # 2. Secondary: DeepSeek (DISABLED V1900)
        # deep_reason = deepseek_engine.generate_deep_reasoning(symbol, signal_type, features)
        # if deep_reason:
        #     return f"[DS] {deep_reason}"

        # 3. Fallback: Local Heuristic
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

    def decide_trade(self, symbol, signal_type, features, df_5m=None, oracle_insight=None, min_conf=0.90):
        """
        V600: The Master AI Decision Engine with Dynamic Backtesting.
        Returns (Bool: Should Trade, Float: Final Prob, String: Reason)
        """
        prob = self.predict_success(features)
        trend = self.get_trend_status(features)
        
        # V600: Dynamic Backtesting Check
        if df_5m is not None:
            recent_acc = self.validate_last_4h(symbol, df_5m)
            if recent_acc < 0.4:
                # If AI has been consistently wrong lately (Mood mismatch)
                prob -= 0.15
                print(f"       [V600 MOOD] AI underperforming lately ({recent_acc:.1%}). Applying safety penalty.")
            elif recent_acc > 0.7:
                prob += 0.10
                print(f"       [V600 MOOD] AI on fire ({recent_acc:.1%})! Confidence boosted.")
        
        # V115: CRISIS MANAGEMENT & STRATEGY REPAIR
        # Replaced blind "Liquidation Override" with "Confluence Boost" logic.
        
        # 0. LIQUIDATION CONFLUENCE (Smart Boost)
        features_rsi = features.get('rsi_value', 50)
        
        if "LIQ" in signal_type:
            # Boost the AI's probability instead of replacing it
            prob += 0.20 
            print(f"       [STRATEGY] Liquidation Signal detected. Boosted Prob to {prob:.2f}")

            # SAFETY CHECK: Counter-Trend Protection
            if "BUY" in signal_type and trend == "BEARISH":
                # Only catch falling knife if RSI is EXTREMELY OVERSOLD
                 if features_rsi > 25:
                     return False, 0.0, "Refused to catch falling knife (Trend Bearish + RSI > 25)"
                 print("       [CRISIS] Counter-Trend Buy Approved (Extreme Oversold Condition met)")

            if "SELL" in signal_type and trend == "BULLISH":
                # Only short a pump if RSI is EXTREMELY OVERBOUGHT
                if features_rsi < 75:
                    return False, 0.0, "Refused to short strong pump (Trend Bullish + RSI < 75)"
                print("       [CRISIS] Counter-Trend Sell Approved (Extreme Overbought Condition met)")
                
        # 1. BASELINE: Apply user-requested confidence from params
        base_decision = prob >= min_conf
        
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

        # 4.5. SMC CONFLUENCE (V560: Smart Money Concepts)
        # Check for FVGs and Order Blocks in the provided features (if OHLCV df is passed)
        smc_data = features.get('smc_details', {})
        if smc_data:
            smc_boost = 0
            if signal_type == "BUY":
                if smc_data.get('ob_bullish'): smc_boost += 0.15
                if smc_data.get('fvg_bullish'): smc_boost += 0.10
            elif signal_type == "SELL":
                if smc_data.get('ob_bearish'): smc_boost += 0.15
                if smc_data.get('fvg_bearish'): smc_boost += 0.10
            
            if smc_boost > 0:
                prob += smc_boost
                print(f"       [SMC CONFLUENCE] Institutional footprints detected. Boosted Prob by +{smc_boost*100:.0f}% to {prob*100:.1f}%")

        # 5. FINAL WEIGHTED DECISION
        required_prob = min_conf
        if trend_aligned and (abs(imb) > 0.4):
            # Only go lower if it's naturally stricter than the user's floor
            required_prob = min(required_prob, 0.85)
            
        should_trade = prob >= required_prob
        
        reasoning = self.generate_reasoning(symbol, signal_type, features, prob) # V700
        final_reason = f"AI {'DECIDED TO TRADE' if should_trade else 'REJECTED'}: Confidence: {prob*100:.1f}%. Target: {required_prob*100:.1f}%. Context: {reasoning}"
        
        return should_trade, prob, final_reason

    def update_asset_bias(self, trade_history):
        """
        V90 Recursive Intelligence.
        Analyzes closed trades and calculates a 'Winning Bias' per symbol.
        trade_history: list of closed trade dicts
        """
        self.asset_biases = {} # symbol -> multiplier
        if not trade_history: return
        
        # Calculate PnL per symbol
        stats = {}
        for trade in trade_history:
            sym = trade['symbol']
            pnl = float(trade.get('pnl', 0))
            if sym not in stats: stats[sym] = []
            stats[sym].append(1 if pnl > 0 else -1)
            
        for sym, results in stats.items():
            # Win Rate based bias: Range 0.8 to 1.2
            win_rate = results.count(1) / len(results)
            bias = 1.0 + (win_rate - 0.5) * 0.4 # 50% WR = 1.0, 100% WR = 1.2, 0% WR = 0.8
            self.asset_biases[sym] = bias
            print(f"      [RECURSIVE AI] Logic adjusted for {sym}: Bias {bias:.2f} (WR: {win_rate*100:.1f}%)")

    def get_top_performing_assets(self, limit=5):
        """V170: Returns symbols with the best performance (PNL/Bias)."""
        biases = getattr(self, 'asset_biases', {})
        if not biases:
            # Fallback: If no history, return top 20 list (or empty to allow all initially)
            return []
            
        # Sort by bias descending
        sorted_assets = sorted(biases.items(), key=lambda x: x[1], reverse=True)
        return [sym for sym, bias in sorted_assets[:limit]]

    def rank_assets(self, asset_data_list):
        """
        V80/V90: Multi-Asset Ranking Engine.
        Prioritizes assets based on (Conf * Trend_Bonus * Recursive_Bias) / Risk_Penalty.
        """
        ranked = []
        # Ensure biases exist
        if not hasattr(self, 'asset_biases'): self.asset_biases = {}
        
        for asset in asset_data_list:
            symbol = asset['symbol']
            features = asset['features']
            sig_type = asset['signal_type']
            
            prob = self.predict_success(features)
            trend = self.get_trend_status(features)
            
            # 1. Base Score
            score = prob * 100
            
            # 2. Recursive Bias (V90)
            bias = self.asset_biases.get(symbol, 1.0)
            score *= bias
            
            # Trend Bonus
            trend_aligned = (sig_type == "BUY" and trend == "BULLISH") or (sig_type == "SELL" and trend == "BEARISH")
            if trend_aligned:
                score += 15 
            else:
                score -= 30 
                
            # Volatility Penalty
            atr = features.get('atr_value', 0)
            price = features.get('price', 1)
            vol_ratio = (atr / price) * 100
            if vol_ratio > 3.0: 
                score -= 10
                
            ranked.append({
                "symbol": symbol,
                "score": round(score, 2),
                "prob": prob,
                "trend": trend,
                "reasoning": self.generate_reasoning(symbol, sig_type, features, prob) # V700
            })
            
        return sorted(ranked, key=lambda x: x['score'], reverse=True)

    def save_signal_to_db(self, signal_data):
        """V500: Writes valid signals to the Strict Schema 'signals' table."""
        try:
            db_record = {
                "symbol": signal_data.get('symbol'),
                "direction": "LONG" if "BUY" in signal_data.get('signal_type', '') else "SHORT",
                "entry_price": signal_data.get('price'),
                "tp_price": signal_data.get('take_profit'),
                "sl_price": signal_data.get('stop_loss'),
                "ai_confidence": signal_data.get('confidence'),
                "risk_level": "HIGH" if signal_data.get('confidence', 0) < 80 else "MID",
                "status": "ACTIVE",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            res = self.supabase.table("signals").insert(db_record).execute()
            if res.data:
                print(f"   [DB] Signal Saved: ID {res.data[0]['id']}")
                return res.data[0]['id']
        except Exception as e:
            print(f"   [DB ERROR] Failed to save signal: {e}")
        return None

# Singleton Instance
brain = CosmosBrain()


if __name__ == "__main__":
    # Manual Training Trigger
    brain.train()
