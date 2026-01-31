"""
NEXUS AI - Academic Manager
Manages academic papers, embeddings, and clustering
"""
import os
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv('.env.local')

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

class AcademicManager:
    """Manages academic papers and embeddings"""
    
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.openai_client = OpenAI(api_key=OPENAI_KEY)
        self.embedding_model = "text-embedding-3-large"
        self.embedding_dim = 1536
        
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        try:
            response = self.openai_client.embeddings.create(
                input=text[:8000],  # Limit to avoid token limits
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"   [EMBEDDING ERROR] {e}")
            return None
    
    def get_paper_by_id(self, paper_id: int) -> Optional[Dict]:
        """Fetch a single paper by ID"""
        try:
            result = self.supabase.table('academic_papers')\
                .select('*')\
                .eq('id', paper_id)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            print(f"   [DB ERROR] {e}")
            return None
    
    def search_papers_semantic(
        self, 
        query: str, 
        threshold: float = 0.70, 
        limit: int = 10
    ) -> List[Dict]:
        """Semantic search using embeddings"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                return []
            
            # Search using RPC function
            result = self.supabase.rpc(
                'match_papers',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': threshold,
                    'match_count': limit
                }
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"   [SEARCH ERROR] {e}")
            return []
    
    def search_papers_hybrid(
        self,
        query: str,
        threshold: float = 0.65,
        limit: int = 10
    ) -> List[Dict]:
        """Hybrid search (semantic + full-text)"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                return []
            
            # Hybrid search using RPC function
            result = self.supabase.rpc(
                'hybrid_search_papers',
                {
                    'query_text': query,
                    'query_embedding': query_embedding,
                    'match_threshold': threshold,
                    'match_count': limit
                }
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"   [HYBRID SEARCH ERROR] {e}")
            return []
    
    def get_similar_papers(
        self,
        paper_id: int,
        threshold: float = 0.75,
        limit: int = 5
    ) -> List[Dict]:
        """Find papers similar to a given paper"""
        try:
            result = self.supabase.rpc(
                'get_similar_papers',
                {
                    'paper_id_param': paper_id,
                    'similarity_threshold': threshold,
                    'limit_count': limit
                }
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"   [SIMILAR PAPERS ERROR] {e}")
            return []
    
    def get_papers_by_cluster(self, cluster_id: int) -> List[Dict]:
        """Get all papers in a cluster"""
        try:
            result = self.supabase.table('academic_papers')\
                .select('*')\
                .eq('topic_cluster', cluster_id)\
                .order('quality_score', desc=True)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"   [CLUSTER ERROR] {e}")
            return []
    
    def get_top_papers(
        self,
        limit: int = 10,
        min_quality: float = 0.7
    ) -> List[Dict]:
        """Get top quality papers"""
        try:
            result = self.supabase.table('academic_papers')\
                .select('*')\
                .gte('quality_score', min_quality)\
                .order('quality_score', desc=True)\
                .order('citation_count', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"   [TOP PAPERS ERROR] {e}")
            return []
    
    def update_paper_quality(self, paper_id: int, quality_score: float):
        """Update paper quality score"""
        try:
            self.supabase.table('academic_papers')\
                .update({'quality_score': quality_score})\
                .eq('id', paper_id)\
                .execute()
        except Exception as e:
            print(f"   [UPDATE ERROR] {e}")
    
    def increment_citation_count(self, paper_id: int):
        """Increment citation count when paper is used"""
        try:
            paper = self.get_paper_by_id(paper_id)
            if paper:
                new_count = paper.get('citation_count', 0) + 1
                self.supabase.table('academic_papers')\
                    .update({'citation_count': new_count})\
                    .eq('id', paper_id)\
                    .execute()
        except Exception as e:
            print(f"   [CITATION ERROR] {e}")
    
    def log_search(
        self,
        query: str,
        results_count: int,
        avg_similarity: float,
        search_type: str = 'semantic',
        user_id: Optional[str] = None
    ):
        """Log search for analytics"""
        try:
            data = {
                'query': query,
                'results_count': results_count,
                'avg_similarity': avg_similarity,
                'search_type': search_type,
                'user_id': user_id
            }
            self.supabase.table('paper_search_history').insert(data).execute()
        except Exception as e:
            print(f"   [LOG ERROR] {e}")
    
    def create_paper_citation(
        self,
        signal_id: int,
        paper_id: int,
        similarity_score: float,
        confidence_boost: float
    ):
        """Create citation link between signal and paper"""
        try:
            data = {
                'signal_id': signal_id,
                'paper_id': paper_id,
                'similarity_score': similarity_score,
                'confidence_boost': confidence_boost
            }
            self.supabase.table('paper_citations').insert(data).execute()
        except Exception as e:
            print(f"   [CITATION LINK ERROR] {e}")
    
    def get_cluster_stats(self) -> List[Dict]:
        """Get statistics for all clusters"""
        try:
            result = self.supabase.rpc('cluster_stats').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"   [CLUSTER STATS ERROR] {e}")
            return []
    
    def get_university_stats(self) -> List[Dict]:
        """Get statistics by university"""
        try:
            result = self.supabase.rpc('university_stats').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"   [UNI STATS ERROR] {e}")
            return []

# Singleton instance
academic_manager = AcademicManager()

if __name__ == "__main__":
    # Test
    print("Testing Academic Manager...")
    
    # Test semantic search
    results = academic_manager.search_papers_semantic(
        "momentum trading strategies",
        threshold=0.70,
        limit=5
    )
    
    print(f"\nFound {len(results)} papers:")
    for r in results:
        print(f"  - {r.get('authors', 'Unknown')} ({r.get('university', 'N/A')})")
        print(f"    Similarity: {r.get('similarity', 0):.2f}")
