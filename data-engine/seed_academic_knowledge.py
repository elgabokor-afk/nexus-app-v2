
import logging
from academic_crawler import crawl_arxiv, ingest_paper
import time

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CosmosLibrarian")

def seed_knowledge_base():
    """
    Seeds the Supabase Vector DB with academic papers.
    """
    logger.info("--- COSMOS LIBRARIAN STARTED ---")
    
    topics = [
        "quantitative trading strategies harvard",
        "market microstructure volatility mit",
        "transformers flexible time series stanford",
        "statistical arbitrage crypto oxford",
        "deep reinforcement learning finance berkeley",
        "high frequency trading imperial college"
    ]
    
    for topic in topics:
        logger.info(f">>> Searching Thesis Topic: {topic}")
        # Fetch more, but filter later if needed.
        # Adding generic query to ensuring we get PHD level stuff
        papers = crawl_arxiv(topic + " thesis", max_results=5)
        
        for p in papers:
            # V4300: Strict Prestige Filter
            # Only ingest if we detected a prestige university OR if it's explicitly a thesis
            if p['university'] != "Unknown" or "thesis" in p['title'].lower() or "dissertation" in p['title'].lower():
                 ingest_paper(p)
                 time.sleep(1) # Rate limit politeness
            else:
                 logger.info(f"   [SKIPPED] {p['title'][:30]}... (Low Prestige Confidence)")

    logger.info("--- KNOWLEDGE INGESTION COMPLETE ---")

if __name__ == "__main__":
    seed_knowledge_base()
