
import os
from supabase import create_client
from dotenv import load_dotenv

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def check_db_stats():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Supabase credentials missing.")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Check academic_papers
        papers = supabase.table("academic_papers").select("id", count="exact").limit(1).execute()
        paper_count = papers.count if papers.count is not None else 0
        
        # Check academic_chunks
        chunks = supabase.table("academic_chunks").select("id", count="exact").limit(1).execute()
        chunk_count = chunks.count if chunks.count is not None else 0
        
        print(f"--- DATABASE STATS ---")
        print(f"Academic Papers: {paper_count}")
        print(f"Academic Chunks (Knowledge Vectors): {chunk_count}")
        
        if paper_count > 0:
            # Sample one paper
            sample = supabase.table("academic_papers").select("title, university").limit(1).execute()
            if sample.data:
                print(f"Sample Entry: {sample.data[0]['title']} ({sample.data[0]['university']})")

    except Exception as e:
        print(f"Error checking DB stats: {e}")

if __name__ == "__main__":
    check_db_stats()
