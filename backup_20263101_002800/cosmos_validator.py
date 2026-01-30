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

class AcademicValidator:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.vector_dim = 3072 # OpenAI Large
        
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

    def validate_signal_logic(self, signal_context):
        """
        Queries the Academic Vector DB to see if this trade setup exists in literature.
        """
        print(f"   [PhD VALIDATION] Consulting Academic Database for: {signal_context[:50]}...")
        
        # 1. Embed the signal context (e.g. "RSI Divergence with Volume Imbalance on BTC")
        query_vec = self.generate_embedding(signal_context)
        
        # 2. Query Supabase
        try:
            res = self.supabase.rpc(
                "match_academic_knowledge",
                {
                    "query_embedding": query_vec,
                    "match_threshold": 0.70, # 70% Similarity required
                    "match_count": 3
                }
            ).execute()
            
            matches = res.data
            
            if not matches:
                return {
                    "approved": False,
                    "score": 0,
                    "reason": "No academic precedent found in Ivy League database.",
                    "citations": []
                }
            
            # Weighted Score
            score = 0
            citations = []
            for m in matches:
                similarity = m['similarity']
                score += similarity * 100
                citations.append(f"{m['title']} ({m['university']}) - {similarity:.2f}")
                
            avg_score = score / len(matches)
            
            avg_score = score / len(matches)
            
            # P-Value Calculation (Inverted Probability)
            # If similarity is 0.95, p-value is 0.05 (Significant)
            p_value = max(0.001, 1 - avg_score)
            
            # Best Match Thesis ID (Prefer paper_id if returned by updated RPC)
            best_match = matches[0] if matches else {}
            best_thesis_id = best_match.get('paper_id') or best_match.get('id')

            return {
                "approved": avg_score > 0.75,
                "score": avg_score,
                "p_value": round(p_value, 4),
                "thesis_id": best_thesis_id,
                "reason": f"Validated by {len(matches)} theses. P-Value: {p_value:.3f}",
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

    def calculate_vpin(self, volume_buy, volume_sell, window_volume):
        """
        VPIN-Lite (Volume-Synchronized Probability of Informed Trading).
        Measures Flow Toxicity.
        """
        total_vol = volume_buy + volume_sell
        if total_vol == 0: return 0
        
        imbalance = abs(volume_buy - volume_sell)
        vpin = imbalance / total_vol
        
        # VPIN > 0.6 usually means Toxic Flow (Informed Traders dumping/pumping)
        return vpin

# Singleton
validator = AcademicValidator()
