#!/usr/bin/env python3
"""
NEXUS AI - Academic Database Auditor
Analyzes the academic_papers table and provides detailed statistics
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment
load_dotenv('.env.local')

from supabase import create_client, Client

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ERROR: Missing Supabase credentials in .env.local")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def print_header(text):
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")

def audit_database():
    """Run comprehensive audit of academic database"""
    
    print_header("NEXUS AI - ACADEMIC DATABASE AUDIT")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Supabase URL: {SUPABASE_URL}\n")
    
    # 1. Overall Statistics
    print_header("1. OVERALL STATISTICS")
    try:
        stats = supabase.rpc('paper_stats').execute()
        if stats.data:
            s = stats.data[0] if isinstance(stats.data, list) else stats.data
            print(f"📚 Total Papers: {s.get('total_papers', 0):,}")
            print(f"✅ With Embeddings: {s.get('papers_with_embeddings', 0):,}")
            print(f"❌ Missing Embeddings: {s.get('papers_missing_embeddings', 0):,}")
            
            total = s.get('total_papers', 1)
            with_emb = s.get('papers_with_embeddings', 0)
            pct = (with_emb / total * 100) if total > 0 else 0
            print(f"📊 Completion: {pct:.1f}%")
            
            print(f"\n🏛️  Universities: {s.get('unique_universities', 0)}")
            print(f"🏷️  Topic Clusters: {s.get('unique_clusters', 0)}")
            print(f"📏 Avg Content Length: {s.get('avg_content_length', 0):,} chars")
            print(f"⭐ Avg Quality Score: {s.get('avg_quality_score', 0):.2f}")
            print(f"✓  Validated Papers: {s.get('validated_papers', 0):,}")
    except Exception as e:
        print(f"⚠️  Could not fetch stats: {e}")
        # Fallback: direct query
        try:
            papers = supabase.table('academic_papers').select('id, embedding').execute()
            total = len(papers.data)
            with_emb = sum(1 for p in papers.data if p.get('embedding'))
            print(f"📚 Total Papers: {total:,}")
            print(f"✅ With Embeddings: {with_emb:,}")
            print(f"❌ Missing Embeddings: {total - with_emb:,}")
            print(f"📊 Completion: {(with_emb/total*100) if total > 0 else 0:.1f}%")
        except Exception as e2:
            print(f"❌ ERROR: {e2}")
    
    # 2. University Breakdown
    print_header("2. PAPERS BY UNIVERSITY")
    try:
        uni_stats = supabase.rpc('university_stats').execute()
        if uni_stats.data:
            for uni in uni_stats.data[:10]:  # Top 10
                name = uni.get('university', 'Unknown')
                count = uni.get('paper_count', 0)
                embedded = uni.get('embedded_count', 0)
                pct = (embedded / count * 100) if count > 0 else 0
                print(f"  {name:30s} {count:4d} papers ({embedded:4d} embedded, {pct:5.1f}%)")
    except Exception as e:
        print(f"⚠️  Could not fetch university stats: {e}")
    
    # 3. Embedding Status
    print_header("3. EMBEDDING GENERATION STATUS")
    try:
        # Get papers without embeddings
        missing = supabase.table('academic_papers')\
            .select('id, paper_id, university, created_at')\
            .is_('embedding', 'null')\
            .limit(10)\
            .execute()
        
        if missing.data:
            print(f"Sample of papers missing embeddings (showing 10/{len(missing.data)}):\n")
            for p in missing.data:
                print(f"  ID: {p.get('id'):6d} | {p.get('university', 'Unknown'):20s} | {p.get('paper_id', 'N/A')}")
        else:
            print("✅ All papers have embeddings!")
    except Exception as e:
        print(f"⚠️  Could not fetch missing embeddings: {e}")
    
    # 4. Cost Estimation
    print_header("4. EMBEDDING GENERATION COST ESTIMATE")
    try:
        # Get papers without embeddings
        missing_count = supabase.table('academic_papers')\
            .select('id', count='exact')\
            .is_('embedding', 'null')\
            .execute()
        
        count = missing_count.count if hasattr(missing_count, 'count') else 0
        
        # OpenAI text-embedding-3-large pricing: $0.00013 per 1K tokens
        # Assume avg 2000 tokens per paper
        avg_tokens = 2000
        cost_per_1k = 0.00013
        total_tokens = count * avg_tokens
        estimated_cost = (total_tokens / 1000) * cost_per_1k
        
        # Time estimate: ~500 papers/hour with batching
        estimated_hours = count / 500
        
        print(f"Papers to process: {count:,}")
        print(f"Estimated tokens: {total_tokens:,}")
        print(f"Estimated cost: ${estimated_cost:.2f} USD")
        print(f"Estimated time: {estimated_hours:.1f} hours")
        print(f"\n💡 Recommendation: Run overnight with batch size 50-100")
    except Exception as e:
        print(f"⚠️  Could not estimate costs: {e}")
    
    # 5. Data Quality Check
    print_header("5. DATA QUALITY ANALYSIS")
    try:
        # Check for papers with missing critical fields
        papers = supabase.table('academic_papers')\
            .select('id, content, authors, university')\
            .limit(1000)\
            .execute()
        
        if papers.data:
            total = len(papers.data)
            missing_content = sum(1 for p in papers.data if not p.get('content'))
            missing_authors = sum(1 for p in papers.data if not p.get('authors'))
            missing_uni = sum(1 for p in papers.data if not p.get('university'))
            
            print(f"Sample size: {total:,} papers")
            print(f"Missing content: {missing_content} ({missing_content/total*100:.1f}%)")
            print(f"Missing authors: {missing_authors} ({missing_authors/total*100:.1f}%)")
            print(f"Missing university: {missing_uni} ({missing_uni/total*100:.1f}%)")
            
            if missing_content > 0:
                print(f"\n⚠️  WARNING: {missing_content} papers have no content!")
    except Exception as e:
        print(f"⚠️  Could not check data quality: {e}")
    
    # 6. Recent Activity
    print_header("6. RECENT ACTIVITY")
    try:
        recent = supabase.table('academic_papers')\
            .select('id, paper_id, university, created_at, embedding_generated_at')\
            .order('created_at', desc=True)\
            .limit(5)\
            .execute()
        
        if recent.data:
            print("Most recently added papers:\n")
            for p in recent.data:
                created = p.get('created_at', 'Unknown')
                emb_gen = p.get('embedding_generated_at', 'Not generated')
                print(f"  {p.get('paper_id', 'N/A'):30s} | {p.get('university', 'Unknown'):20s}")
                print(f"    Added: {created} | Embedding: {emb_gen}\n")
    except Exception as e:
        print(f"⚠️  Could not fetch recent activity: {e}")
    
    # 7. Recommendations
    print_header("7. RECOMMENDATIONS")
    
    try:
        stats = supabase.rpc('paper_stats').execute()
        if stats.data:
            s = stats.data[0] if isinstance(stats.data, list) else stats.data
            missing = s.get('papers_missing_embeddings', 0)
            
            if missing == 0:
                print("✅ All papers have embeddings! Ready for RAG system.")
            elif missing < 100:
                print(f"✅ Only {missing} papers missing embeddings. Quick generation recommended.")
                print(f"   Run: python scripts/generate_all_embeddings.py --limit {missing}")
            else:
                print(f"⚠️  {missing:,} papers need embeddings. Batch generation recommended.")
                print(f"   1. Test first: python scripts/generate_all_embeddings.py --dry-run")
                print(f"   2. Small batch: python scripts/generate_all_embeddings.py --limit 100")
                print(f"   3. Full run: nohup python scripts/generate_all_embeddings.py > logs/embeddings.log 2>&1 &")
    except:
        pass
    
    print_header("AUDIT COMPLETE")
    print(f"Next steps:")
    print(f"  1. Review the statistics above")
    print(f"  2. Run: python scripts/generate_all_embeddings.py --dry-run")
    print(f"  3. Generate embeddings: python scripts/generate_all_embeddings.py")
    print(f"  4. Monitor progress: python scripts/monitor_database.py\n")

if __name__ == "__main__":
    try:
        audit_database()
    except KeyboardInterrupt:
        print("\n\n⚠️  Audit interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
