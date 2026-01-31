import os
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv
import warnings # V200: Version Guard

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

# Fix 2: University Weights for Academic Validation
UNIVERSITY_WEIGHTS = {
    'MIT': 1.15,
    'Harvard': 1.12,
    'Oxford': 1.10,
    'Stanford': 1.08,
    'Cambridge': 1.07,
    'Unknown': 1.0
}

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Cosmos Engine: Supabase credentials missing (Check .env.local)") 

from deep_brain import deep_brain # V490
from smc_engine import smc_engine # V560
from deepseek_engine import deepseek_engine # V700
from openai_engine import openai_engine # V800
from ollama_engine import ollama_engine # V2000 (Local Sovereign AI)
from cosmos_validator import validator # V900 (PhD Upgrade)
from redis_engine import redis_engine # V1000 (Liquidity Check)

class CosmosBrain:
    # ... (init stays same) ...

    # ... (skipping to generate_reasoning) ...

    def generate_reasoning(self, symbol, signal_type, features, prob):
        """
        V2000: Sovereign Reasoning Layer.
        Prioritizes Local Ollama (RTX 4070), then falls back to OpenAI/Heuristic.
        """
        # 1. Primary: Local Ollama (Zero Cost, High Privacy)
        if ollama_engine and ollama_engine.is_active:
            local_reason = ollama_engine.generate_trade_narrative(symbol, signal_type, features)
            if local_reason:
                return f"[OLLAMA LOCAL] {local_reason}"
        
        # 2. Secondary: OpenAI (If Local is Offline)
        # V1900: User requested OpenAI ONLY (DeepSeek deprecated due to balance)
        try:
             openai_reason = openai_engine.generate_trade_narrative(symbol, signal_type, features)
             if openai_reason:
                 return f"[GPT-4o] {openai_reason}"
        except: pass

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
            
        # 5. [V4000] Multi-Chain Force
        dex_f = features.get('dex_force', 0)
        if dex_f > 0.4:
            insights.append(f"Strong on-chain liquidity depth ({dex_f*100:.0f}% bullish) detected across Hyperliquid/DEXs.")
        elif dex_f < -0.4:
            insights.append(f"Significant sell-side pressure ({abs(dex_f)*100:.0f}% bearish) detected in on-chain order books.")

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
            
        # V410: Path Robustness
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Priority 1: Check for 'xgb_model.pkl' (Generated by force_retrain.py)
        model_path = os.path.join(current_dir, "xgb_model.pkl")
        
        # Priority 2: Legacy fallback
        if not os.path.exists(model_path):
             model_path = os.path.join(current_dir, "xgb_model_v4.pkl")
             
        # Priority 3: Root fallback
        if not os.path.exists(model_path):
             model_path = "xgb_model.pkl"

        print(f"   [BRAIN] Loading Neural Model from: {model_path}")
        self.model = joblib.load(model_path)
        print("   [BRAIN] Model Loaded Successfully.")
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
        
        # V4000: Multi-Chain Boost
        dex_f = features.get('dex_force', 0)
        if abs(dex_f) > 0.5:
             prob += (0.10 if dex_f > 0 else -0.10)
             print(f"       [DEX FORCE] Significant Multi-Chain imbalance ({dex_f:.2f}). Adjusting Prob.")

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

        # 5. [FIX 2] ACADEMIC VALIDATION ENDURECIDA (PhD Layer)
        # Create a "Paper Thesis" string to check against DB
        thesis_context = f"Strategy: {signal_type} on {symbol}. Technicals: RSI {features.get('rsi_value')}, Imbalance {features.get('imbalance_ratio', 0)}. Trend: {trend}."
        
        validation_result = validator.validate_signal_logic(thesis_context)
        
        # Fix 2: Endurecer validación - No permitir trades sin respaldo académico
        if not validation_result['approved']:
            # Penalización severa si no hay respaldo académico
            prob *= 0.5  # Reducir confianza a la mitad
            print(f"       [PhD PENALTY] No academic support. Confidence reduced to {prob*100:.1f}%")
            
            # Solo permitir si la confianza es EXTREMADAMENTE alta (>90%)
            if prob < 0.90:
                return False, prob, f"REJECTED by Cosmos PhD: {validation_result['reason']} (Conf {prob*100:.1f}% < 90% required without PhD)"
            else:
                print(f"       [PhD BYPASS] No academic support, but AI Confidence ({prob*100:.1f}%) is exceptional.")

        if validation_result['approved']:
            # Fix 2: Aplicar peso universitario
            university = validation_result.get('university', 'Unknown')
            uni_weight = UNIVERSITY_WEIGHTS.get(university, 1.0)
            prob *= uni_weight
            
            print(f"       [PhD VALIDATED] {validation_result['citations'][0] if validation_result['citations'] else 'Academic paper'}")
            print(f"       [UNIVERSITY BOOST] {university}: {uni_weight}x multiplier → Final Prob: {prob*100:.1f}%")
            print(f"       [STATISTICAL] p-value: {validation_result.get('p_value', 1.0):.4f}")

        # Capture P-Value and Thesis ID for DB
        self.last_p_value = validation_result.get('p_value', 1.0)
        self.last_thesis_id = validation_result.get('thesis_id', None)
        self.last_university = validation_result.get('university', 'Unknown')  # Fix 2: Guardar universidad
             
        # 6. VPIN TOXICITY CHECK
        # Estimate volume buckets from features if available (mocking for now as we lack granular data in features)
        # In production, this would use real Order Book flow
        toxicity = validator.calculate_vpin(0.5, 0.5, 1.0) # Placeholder
        if toxicity > 0.6:
             print("       [TOXIC FLOW] High VPIN detected. Reducing position size request.")
             # Logic to reduce size would happen in PaperTrader, here we just note it.

        # 7. [NEW] LIQUIDITY CASCADE CHECK (Execution Layer)
        # Query Redis for cached order book depth
        liq_data = redis_engine.get_liquidity(symbol)
        if liq_data:
            bid_vol = liq_data.get('bid', 0)
            ask_vol = liq_data.get('ask', 0)
            
            # Simple Rule: Need at least $50k depth to enter safely without slippage
            min_depth_usd = 50000 
            # Convert volume to USD (approx)
            depth_usd = (bid_vol if "SELL" in signal_type else ask_vol) * features.get('price', 0)
            
            if depth_usd < min_depth_usd:
                return False, prob, f"REJECTED by Liquidity Filter: Depth ${depth_usd:.0f} < ${min_depth_usd}. Slippage Risk."
            else:
                print(f"       [LIQUIDITY OK] Depth ${depth_usd:.0f} sufficient for entry.")

        # 8. FINAL WEIGHTED DECISION
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

    def get_asset_bias(self, symbol):
        """V90: Returns the Recursive Learning Multiplier for a specific asset."""
        if not hasattr(self, 'asset_biases'): return 1.0
        return self.asset_biases.get(symbol, 1.0)

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
                "rsi": signal_data.get('rsi'),
                "atr_value": signal_data.get('atr_value'),
                "volume_ratio": signal_data.get('volume_ratio'),
                "academic_thesis_id": signal_data.get('academic_thesis_id') or getattr(self, 'last_thesis_id', None),
                "statistical_p_value": signal_data.get('statistical_p_value') or getattr(self, 'last_p_value', 1.0),
                "nli_safety_score": signal_data.get('nli_score', 1.0),
                "dex_force_score": signal_data.get('dex_force', 0),
                "whale_sentiment_score": signal_data.get('whale_sentiment', 0),
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
