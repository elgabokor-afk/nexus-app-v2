#!/usr/bin/env python3
"""
NEXUS AI - Mass Embedding Generator
Generates embeddings for all academic papers in the database
"""
import os
import sys
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment
load_dotenv('.env.local')

from supabase import create_client, Client
from openai import OpenAI

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_KEY]):
    print("❌ ERROR: Missing credentials in .env.local")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_KEY)

# Configuration
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 1536
BATCH_SIZE = 50
RATE_LIMIT_DELAY = 0.5  # seconds between requests
MAX_RETRIES = 3

class EmbeddingGenerator:
    def __init__(self, dry_run=False, limit=None):
        self.dry_run = dry_run
        self.limit = limit
        self.stats = {
            'total': 0,
            'processed': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'cost': 0.0
        }
        self.start_time = time.time()
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")
    
    def generate_embedding(self, text):
        """Generate embedding for text using OpenAI"""
        try:
            response = openai_client.embeddings.create(
                input=text[:8000],  # Limit to ~8k chars to avoid token limits
                model=EMBEDDING_MODEL
            )
            return response.data[0].embedding
        except Exception as e:
            self.log(f"OpenAI API error: {e}", "ERROR")
            return None
    
    def fetch_papers_without_embeddings(self):
        """Fetch papers that need embeddings"""
        try:
            query = supabase.table('academic_papers')\
                .select('id, paper_id, content, authors, university')\
                .is_('embedding', 'null')\
                .order('id')
            
            if self.limit:
                query = query.limit(self.limit)
            
            result = query.execute()
            return result.data
        except Exception as e:
            self.log(f"Database error: {e}", "ERROR")
            return []
    
    def update_paper_embedding(self, paper_id, embedding):
        """Update paper with generated embedding"""
        try:
            supabase.table('academic_papers').update({
                'embedding': embedding,
                'embedding_model': EMBEDDING_MODEL,
                'embedding_generated_at': datetime.now().isoformat()
            }).eq('id', paper_id).execute()
            return True
        except Exception as e:
            self.log(f"Failed to update paper {paper_id}: {e}", "ERROR")
            return False
    
    def estimate_cost(self, papers):
        """Estimate cost for generating embeddings"""
        total_chars = sum(len(p.get('content', '')) for p in papers)
        # Rough estimate: 1 char ≈ 0.25 tokens
        total_tokens = total_chars * 0.25
        # text-embedding-3-large: $0.00013 per 1K tokens
        cost = (total_tokens / 1000) * 0.00013
        return cost, total_tokens
    
    def process_paper(self, paper):
        """Process a single paper"""
        paper_id = paper.get('id')
        content = paper.get('content', '')
        authors = paper.get('authors', '')
        university = paper.get('university', '')
        
        if not content:
            self.log(f"Paper {paper_id} has no content, skipping", "WARN")
            self.stats['skipped'] += 1
            return False
        
        # Create text for embedding (content + metadata)
        text = f"{content}\n\nAuthors: {authors}\nUniversity: {university}"
        
        if self.dry_run:
            self.log(f"[DRY RUN] Would generate embedding for paper {paper_id}", "INFO")
            self.stats['success'] += 1
            return True
        
        # Generate embedding with retries
        for attempt in range(MAX_RETRIES):
            embedding = self.generate_embedding(text)
            
            if embedding:
                # Update database
                if self.update_paper_embedding(paper_id, embedding):
                    self.stats['success'] += 1
                    # Estimate cost (rough)
                    tokens = len(text) * 0.25
                    self.stats['cost'] += (tokens / 1000) * 0.00013
                    return True
                else:
                    self.stats['failed'] += 1
                    return False
            
            if attempt < MAX_RETRIES - 1:
                self.log(f"Retry {attempt + 1}/{MAX_RETRIES} for paper {paper_id}", "WARN")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        self.stats['failed'] += 1
        return False
    
    def run(self):
        """Main execution"""
        self.log("="*80)
        self.log("NEXUS AI - EMBEDDING GENERATION")
        self.log("="*80)
        
        if self.dry_run:
            self.log("🔍 DRY RUN MODE - No actual changes will be made", "WARN")
        
        # Fetch papers
        self.log("Fetching papers without embeddings...")
        papers = self.fetch_papers_without_embeddings()
        
        if not papers:
            self.log("✅ No papers need embeddings!", "INFO")
            return
        
        self.stats['total'] = len(papers)
        self.log(f"Found {self.stats['total']} papers to process")
        
        # Estimate cost
        estimated_cost, estimated_tokens = self.estimate_cost(papers)
        estimated_time = (self.stats['total'] / 500) * 60  # minutes
        
        self.log(f"📊 Estimated tokens: {estimated_tokens:,.0f}")
        self.log(f"💰 Estimated cost: ${estimated_cost:.2f} USD")
        self.log(f"⏱️  Estimated time: {estimated_time:.1f} minutes")
        
        if not self.dry_run:
            response = input("\n⚠️  Proceed with generation? (yes/no): ")
            if response.lower() != 'yes':
                self.log("❌ Aborted by user", "WARN")
                return
        
        self.log("\n🚀 Starting generation...")
        
        # Process papers in batches
        for i, paper in enumerate(papers, 1):
            self.stats['processed'] += 1
            
            # Progress
            if i % 10 == 0 or i == self.stats['total']:
                elapsed = time.time() - self.start_time
                rate = i / elapsed if elapsed > 0 else 0
                remaining = (self.stats['total'] - i) / rate if rate > 0 else 0
                
                self.log(
                    f"Progress: {i}/{self.stats['total']} "
                    f"({i/self.stats['total']*100:.1f}%) | "
                    f"Rate: {rate:.1f}/s | "
                    f"ETA: {remaining/60:.1f}min"
                )
            
            # Process
            success = self.process_paper(paper)
            
            if success and not self.dry_run:
                time.sleep(RATE_LIMIT_DELAY)  # Rate limiting
        
        # Final report
        self.log("\n" + "="*80)
        self.log("GENERATION COMPLETE")
        self.log("="*80)
        
        elapsed = time.time() - self.start_time
        self.log(f"Total papers: {self.stats['total']}")
        self.log(f"Processed: {self.stats['processed']}")
        self.log(f"✅ Success: {self.stats['success']}")
        self.log(f"❌ Failed: {self.stats['failed']}")
        self.log(f"⏭️  Skipped: {self.stats['skipped']}")
        
        if not self.dry_run:
            self.log(f"💰 Actual cost: ${self.stats['cost']:.2f} USD")
        
        self.log(f"⏱️  Time elapsed: {elapsed/60:.1f} minutes")
        self.log(f"📈 Rate: {self.stats['processed']/elapsed:.2f} papers/second")
        
        if self.stats['failed'] > 0:
            self.log(f"\n⚠️  {self.stats['failed']} papers failed. Check logs and retry.", "WARN")

def main():
    parser = argparse.ArgumentParser(description='Generate embeddings for academic papers')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without making changes')
    parser.add_argument('--limit', type=int, help='Limit number of papers to process')
    
    args = parser.parse_args()
    
    generator = EmbeddingGenerator(dry_run=args.dry_run, limit=args.limit)
    
    try:
        generator.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
        print(f"Progress: {generator.stats['success']}/{generator.stats['total']} completed")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
