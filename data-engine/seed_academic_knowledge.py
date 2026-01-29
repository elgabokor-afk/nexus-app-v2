import os
import time
from cosmos_validator import validator
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# THE CORE THESES (User Requested)
CORE_KNOWLEDGE = [
    {
        "title": "Flow Toxicity and Liquidity in High Frequency Markets",
        "university": "Cornell / Oxford",
        "authors": "Easley, Lopez de Prado, O'Hara",
        "tags": ["Market Microstructure", "VPIN"],
        "content": """
        The Volume-Synchronized Probability of Informed Trading (VPIN) metric is a proxy for order flow toxicity. 
        It measures the imbalance between buy and sell volume in defined volume buckets rather than time buckets.
        High VPIN values (> 0.6) indicate a high probability of informed trading (toxic flow), often preceding high volatility or market crashes.
        Trading Strategy: Avoid taking liquidity when VPIN is high. Market Makers should widen spreads.
        If VPIN > threshold, standard mean-reversion signals are likely to fail ("Catching a falling knife").
        """
    },
    {
        "title": "Optimal Execution of Portfolio Transactions",
        "university": "Stanford / NYU",
        "authors": "Almgren & Chriss",
        "tags": ["Optimal Execution", "Liquidity"],
        "content": """
        The Almgren-Chriss model balances Transaction Cost (Market Impact) against Volatility Risk (Timing Risk).
        For large institutional orders, execution should be broken into child orders (TWAP/VWAP).
        Urgency parameter determines the aggressiveness.
        In high volatility regimes (High ATR), execution should be accelerated (Front-loaded) to minimize variance risk.
        In low volatility, execution can be passive to capture spread (Limit Orders).
        """
    },
    {
        "title": "The Adaptive Markets Hypothesis",
        "university": "MIT",
        "authors": "Andrew Lo",
        "tags": ["Behavioral Finance", "Evolutionary Economics"],
        "content": """
        Markets serve as an evolutionary mechanism. Strategies that worked in the past may decay as competition adapts.
        Efficiency is not a destination but a state dependent on market participants.
        Regime Switching: Markets oscillate between "Efficient" (Random Walk) and "Inefficient" (Trend/Mean Reversion possible).
        Alpha Strategy: Detect the current regime (Trend vs Range).
        If RSI Divergence fails repeatedly, the market has adapted; the agent must switch to Trend Following logic.
        """
    },
    {
        "title": "A New Interpretation of the Kelly Criterion",
        "university": "Princeton (Thorp) / Harvard",
        "authors": "Ed Thorp",
        "tags": ["Risk Management", "Kelly Criterion"],
        "content": """
        The Kelly Criterion maximizes the logarithm of wealth growth.
        Full Kelly is too volatile for real markets due to parameter uncertainty (Estimation Error).
        Fractional Kelly (Half-Kelly) offers 75% of the growth with 50% of the variance.
        Formula: f* = (bp - q) / b where b is odds recieved, p is probability of win, q is probability of loss.
        Position sizing should scale with Confidence and Reward-to-Risk ratio.
        Never bet more than the model edge.
        """
    }
]

def seed_knowledge():
    print("--- SEEDING COSMOS PHD KNOWLEDGE BASE ---")
    
    for paper in CORE_KNOWLEDGE:
        print(f"Processing: {paper['title']}...")
        
        # 1. Create Paper Record
        res = supabase.table("academic_papers").insert({
            "title": paper['title'],
            "university": paper['university'],
            "authors": paper['authors'],
            "topic_tags": paper['tags'],
            "pdf_url": "https://seed-knowledge.internal"
        }).execute()
        
        paper_id = res.data[0]['id']
        
        # 2. Generate Embedding
        embedding = validator.generate_embedding(paper['content'])
        
        # 3. Store Vector Chunk
        supabase.table("academic_chunks").insert({
            "paper_id": paper_id,
            "content": paper['content'].strip(),
            "embedding": embedding
        }).execute()
        
        print(f"   [OK] Indexed: {paper['title']}")
        time.sleep(0.5) # Rate limit politeness

    print("--- SEEDING COMPLETE ---")

if __name__ == "__main__":
    seed_knowledge()
