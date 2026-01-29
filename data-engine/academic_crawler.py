import requests
import xml.etree.ElementTree as ET
from cosmos_validator import validator 
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def crawl_arxiv(query="quantitative trading", max_results=5):
    """
    Fetches proper academic papers from Arxiv API.
    """
    print(f"   [CRAWLER] Searching Arxiv for: {query}")
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results
    }
    
    try:
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            print("   [CRAWLER] API connection failed.")
            return []
            
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        papers = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip()
            summary = entry.find('atom:summary', ns).text.strip()
            pdf_url = entry.find('atom:id', ns).text
            
            # Improved University Extraction (Heuristic)
            summary_lower = summary.lower()
            title_lower = title.lower()
            
            uni = "Unknown"
            prestige_keywords = {
                "mit": "MIT",
                "massachusetts institute of technology": "MIT",
                "harvard": "Harvard",
                "stanford": "Stanford",
                "oxford": "Oxford",
                "cambridge": "Cambridge",
                "princeton": "Princeton",
                "chicago": "UChicago",
                "berkeley": "UC Berkeley",
                "columbia": "Columbia",
                "wharton": "Wharton",
                "imperial college": "Imperial"
            }
            
            # Check Title and Summary for affiliation hints
            for key, name in prestige_keywords.items():
                if key in summary_lower or key in title_lower:
                    uni = name
                    break
            
            # If user demands PRESTIGE only, we can filter here or in the seeder.
            # For now, we tag them.
            
            papers.append({
                "title": title,
                "summary": summary, 
                "university": uni,
                "pdf_url": pdf_url
            })
            
        return papers
        
    except Exception as e:
        print(f"   [CRAWLER ERROR] {e}")
        return []

def ingest_paper(paper_data):
    """
    1. Saves Paper Metadata to `academic_papers`.
    2. Chunks Summary/Content.
    3. EmbedsChunks.
    4. Saves to `academic_chunks`.
    """
    try:
        # 1. Insert Paper
        res = supabase.table("academic_papers").insert({
            "title": paper_data['title'],
            "university": paper_data['university'],
            "pdf_url": paper_data['pdf_url'],
            "topic_tags": ["Quantitative Finance", "RAG Auto-Ingest"]
        }).execute()
        
        paper_id = res.data[0]['id']
        print(f"   [INGEST] Saved Paper ID {paper_id}: {paper_data['title'][:40]}...")
        
        # 2. Embed Summary (as the main chunk for now)
        # In a real full crawler, we'd download PDF, parse text, and chunk it.
        # Here we use the abstract/summary.
        summary_text = paper_data['summary']
        embedding = validator.generate_embedding(summary_text)
        
        # 3. Insert Chunk
        supabase.table("academic_chunks").insert({
            "paper_id": paper_id,
            "content": summary_text,
            "embedding": embedding
        }).execute()
        
        print(f"   [RAG] Indexed 1 vector chunk for {paper_data['title']}")
        
    except Exception as e:
        print(f"   [INGEST ERROR] {e}")

if __name__ == "__main__":
    # Test Run
    results = crawl_arxiv("market microstructure", 3)
    for p in results:
        ingest_paper(p)
