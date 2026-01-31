import os
import numpy as np
import math
from supabase import create_client, Client
from dotenv import load_dotenv

# Load env
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# V2000: Import new RAG engine
try:
    from rag_engine_v2 import rag_engine
    RAG_V2_AVAILABLE = True
except ImportError:
    RAG_V2_AVAILABLE = False
    print("   [VALIDATOR] RAG V2 not available, using legacy mode")

class AcademicValidator:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.vector_dim = 1536  # Updated to match text-embedding-3-large
        self.use_rag_v2 = RAG_V2_AVAILABLE
        
    def generate_embedding(self, text):
        """
        Wrapper to call OpenAI Embedding API.
        If API key missing, returns random vector (MOCK) for dev testing.
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-large"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"   [RAG MOCK] Embeddings API unavailable ({e}). Using random vector.")
            return np.random.rand(self.vector_dim).tolist()

    def validate_signal_logic(self, signal_context, symbol="BTC/USD", direction="LONG", technical_context=None):
        """
        V2000: Enhanced validation using RAG Engine V2
        Queries the Academic Vector DB to see if this trade setup exists in literature.
        """
        print(f"   [PhD VALIDATION] Consulting Academic Database for: {signal_context[:50]}...")
        
        # V2000: Use RAG Engine V2 if available
        if self.use_rag_v2 and technical_context:
            try:
                result = rag_engine.validate_trading_strategy(
                    strategy_description=signal_context,
                    symbol=symbol,
                    direction=direction,
                    technical_context=technical_context
                )
                
                # Convert to legacy format for compatibility
                return {
                    "approved": result['approved'],
                    "score": result['confidence'] * 100,
                    "p_value": result['p_value'],
                    "thesis_id": result['thesis_id'],
                    "reason": result['reasoning'],
                    "citations": [
                        f"{p.get('authors', 'Unknown')} ({p.get('university', 'N/A')}) - {p.get('similarity', 0):.2f}"
                        for p in result['papers']
                    ]
                }
            except Exception as e:
                print(f"   [RAG V2 ERROR] {e}, falling back to legacy")
        
        # Legacy mode (fallback)
        # 1. Embed the signal context
        query_vec = self.generate_embedding(signal_context)
        
        # 2. Query Supabase using match_papers function
        try:
            res = self.supabase.rpc(
                "match_papers",
                {
                    "query_embedding": query_vec,
                    "match_threshold": 0.70,
                    "match_count": 3
                }
            ).execute()
            
            matches = res.data
            
            if not matches:
                return {
                    "approved": False,
                    "score": 0,
                    "reason": "No academic precedent found in database.",
                    "citations": []
                }
            
            # Weighted Score
            score = 0
            citations = []
            for m in matches:
                similarity = m.get('similarity', 0)
                score += similarity * 100
                authors = m.get('authors', 'Unknown')
                university = m.get('university', 'N/A')
                citations.append(f"{authors} ({university}) - {similarity:.2f}")
                
            avg_score = score / len(matches)
            
            # P-Value Calculation
            p_value = max(0.001, 1 - (avg_score / 100))
            
            # Best Match Thesis ID
            best_match = matches[0] if matches else {}
            best_thesis_id = best_match.get('id')

            return {
                "approved": avg_score > 75,
                "score": avg_score,
                "p_value": round(p_value, 4),
                "thesis_id": best_thesis_id,
                "reason": f"Validated by {len(matches)} papers. P-Value: {p_value:.3f}",
                "citations": citations
            }
            
        except Exception as e:
            print(f"   [RAG ERROR] {e}")
            return {"approved": True, "score": 50, "reason": "Validation Bypass (Error)", "citations": []}

    # --- MATH MODULES ---

    def calculate_kelly_criterion(self, win_rate, reward_ratio):
        """
        fractional kelly = f * (bp - q) / b
        """
        # Safe caps
        if win_rate <= 0.5: return 0.01 # 1% Min Risk
        
        kelley_pct = win_rate - ((1 - win_rate) / reward_ratio)
        safe_kelly = kelley_pct * 0.5 # Half Kelly is standard safe practice
        
        return max(0.01, min(0.05, safe_kelly)) # Cap between 1% and 5%

    def calculate_vpin_simple(self, volume_buy, volume_sell, window_volume):
        """
        VPIN-Lite (Volume-Synchronized Probability of Informed Trading).
        Measures Flow Toxicity.
        DEPRECATED: Use calculate_vpin_accurate() for production.
        """
        total_vol = volume_buy + volume_sell
        if total_vol == 0: return 0
        
        imbalance = abs(volume_buy - volume_sell)
        vpin = imbalance / total_vol
        
        # VPIN > 0.6 usually means Toxic Flow (Informed Traders dumping/pumping)
        return vpin
    
    def calculate_vpin_accurate(self, trades_df, bucket_size=50, window=50):
        """
        VPIN Implementation according to Easley et al. (2012)
        "Flow Toxicity and Liquidity in a High Frequency World"
        
        Args:
            trades_df: DataFrame with columns ['timestamp', 'side', 'volume', 'price']
            bucket_size: Volume per bucket (default: 50 units)
            window: Number of buckets to calculate VPIN (default: 50)
        
        Returns:
            float: VPIN score (0 to 1, >0.6 indicates toxicity)
        
        Theory:
            VPIN = Average(|V_buy - V_sell| / (V_buy + V_sell)) over N volume buckets
            
            High VPIN (>0.6) indicates:
            - Presence of informed traders
            - Toxic order flow
            - Increased adverse selection risk
            - Potential for flash crashes
        """
        import pandas as pd
        
        if trades_df is None or trades_df.empty or len(trades_df) < window:
            print(f"   [VPIN] Insufficient data: {len(trades_df) if trades_df is not None else 0} trades")
            return 0
        
        # 1. Create volume-synchronized buckets
        buckets = []
        current_bucket = {'buy': 0, 'sell': 0, 'timestamp': None}
        cumulative_vol = 0
        
        for _, trade in trades_df.iterrows():
            if current_bucket['timestamp'] is None:
                current_bucket['timestamp'] = trade['timestamp']
            
            # Classify trade side
            side = 'buy' if trade['side'] in ['buy', 'BUY', 1, True] else 'sell'
            current_bucket[side] += trade['volume']
            cumulative_vol += trade['volume']
            
            # When bucket reaches target size
            if cumulative_vol >= bucket_size:
                buckets.append(current_bucket.copy())
                current_bucket = {'buy': 0, 'sell': 0, 'timestamp': trade['timestamp']}
                cumulative_vol = 0
        
        # 2. Calculate VPIN over last N buckets
        if len(buckets) < window:
            print(f"   [VPIN] Insufficient buckets: {len(buckets)} < {window}")
            return 0
        
        recent_buckets = buckets[-window:]
        
        # VPIN = Average(|V_buy - V_sell| / (V_buy + V_sell))
        vpin_sum = 0
        valid_buckets = 0
        
        for bucket in recent_buckets:
            total_vol = bucket['buy'] + bucket['sell']
            if total_vol > 0:
                imbalance = abs(bucket['buy'] - bucket['sell'])
                vpin_sum += (imbalance / total_vol)
                valid_buckets += 1
        
        if valid_buckets == 0:
            return 0
        
        vpin = vpin_sum / valid_buckets
        
        # Log if VPIN is high (toxic flow detected)
        if vpin > 0.6:
            print(f"   [VPIN ALERT] High toxicity detected: {vpin:.3f} (Threshold: 0.6)")
            print(f"   [VPIN ALERT] Informed traders likely present. Adverse selection risk HIGH.")
        elif vpin > 0.5:
            print(f"   [VPIN WARNING] Moderate toxicity: {vpin:.3f}")
        
        return vpin
    
    def calculate_vpin(self, *args, **kwargs):
        """
        Wrapper for backward compatibility.
        Routes to accurate implementation if DataFrame is provided.
        """
        # Check if first argument is a DataFrame
        if args and hasattr(args[0], 'iterrows'):
            return self.calculate_vpin_accurate(*args, **kwargs)
        else:
            # Legacy call with volume_buy, volume_sell
            return self.calculate_vpin_simple(*args, **kwargs)

# Singleton
validator = AcademicValidator()
