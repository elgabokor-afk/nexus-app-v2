
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
        "quantitative trading strategies",
        "market microstructure volatility",
        "transformers flexible time series",
        "statistical arbitrage crypto"
    ]
    
    for topic in topics:
        logger.info(f">>> Searching Thesis Topic: {topic}")
        papers = crawl_arxiv(topic, max_results=3)
        
        for p in papers:
            ingest_paper(p)
            time.sleep(1) # Rate limit politeness

    logger.info("--- KNOWLEDGE INGESTION COMPLETE ---")

if __name__ == "__main__":
    seed_knowledge_base()
