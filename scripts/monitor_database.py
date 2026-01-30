#!/usr/bin/env python3
"""
NEXUS AI - Database Monitor
Real-time monitoring of embedding generation progress
"""
import os
import sys
import time
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
    print("❌ ERROR: Missing Supabase credentials")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_stats():
    """Fetch current statistics"""
    try:
        # Try using the view first
        stats = supabase.rpc('paper_stats').execute()
        if stats.data:
            return stats.data[0] if isinstance(stats.data, list) else stats.data
    except:
        pass
    
    # Fallback: manual query
    try:
        papers = supabase.table('academic_papers').select('id, embedding').execute()
        total = len(papers.data)
        with_emb = sum(1 for p in papers.data if p.get('embedding'))
        
        return {
            'total_papers': total,
            'papers_with_embeddings': with_emb,
            'papers_missing_embeddings': total - with_emb
        }
    except Exception as e:
        return {'error': str(e)}

def get_recent_activity():
    """Get recently generated embeddings"""
    try:
        recent = supabase.table('academic_papers')\
            .select('id, paper_id, university, embedding_generated_at')\
            .not_.is_('embedding_generated_at', 'null')\
            .order('embedding_generated_at', desc=True)\
            .limit(5)\
            .execute()
        return recent.data
    except:
        return []

def monitor(refresh_interval=5):
    """Monitor database in real-time"""
    
    print("🔍 NEXUS AI - Database Monitor")
    print("Press Ctrl+C to exit\n")
    
    last_count = 0
    start_time = time.time()
    
    try:
        while True:
            clear_screen()
            
            print("="*80)
            print(f"  NEXUS AI - DATABASE MONITOR")
            print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*80)
            
            # Get stats
            stats = get_stats()
            
            if 'error' in stats:
                print(f"\n❌ ERROR: {stats['error']}")
                time.sleep(refresh_interval)
                continue
            
            total = stats.get('total_papers', 0)
            with_emb = stats.get('papers_with_embeddings', 0)
            missing = stats.get('papers_missing_embeddings', 0)
            
            # Calculate progress
            progress_pct = (with_emb / total * 100) if total > 0 else 0
            progress_bar_len = 50
            filled = int(progress_bar_len * progress_pct / 100)
            bar = '█' * filled + '░' * (progress_bar_len - filled)
            
            print(f"\n📊 OVERALL PROGRESS")
            print(f"   {bar} {progress_pct:.1f}%")
            print(f"\n   Total Papers:      {total:,}")
            print(f"   ✅ With Embeddings: {with_emb:,}")
            print(f"   ❌ Missing:         {missing:,}")
            
            # Calculate rate
            if last_count > 0:
                new_embeddings = with_emb - last_count
                rate = new_embeddings / refresh_interval
                
                if rate > 0:
                    eta_seconds = missing / rate
                    eta_minutes = eta_seconds / 60
                    
                    print(f"\n⚡ GENERATION RATE")
                    print(f"   Rate: {rate:.2f} embeddings/second")
                    print(f"   ETA:  {eta_minutes:.1f} minutes")
            
            last_count = with_emb
            
            # Recent activity
            recent = get_recent_activity()
            if recent:
                print(f"\n📝 RECENT ACTIVITY (Last 5)")
                for r in recent:
                    paper_id = r.get('paper_id', 'N/A')[:30]
                    uni = r.get('university', 'Unknown')[:20]
                    timestamp = r.get('embedding_generated_at', '')[:19]
                    print(f"   {timestamp} | {uni:20s} | {paper_id}")
            
            # Runtime
            elapsed = time.time() - start_time
            print(f"\n⏱️  Monitor runtime: {elapsed/60:.1f} minutes")
            print(f"\n🔄 Refreshing every {refresh_interval} seconds...")
            print("   Press Ctrl+C to exit")
            
            time.sleep(refresh_interval)
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitor stopped")
        sys.exit(0)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor database embedding generation')
    parser.add_argument('--interval', type=int, default=5, help='Refresh interval in seconds')
    
    args = parser.parse_args()
    
    monitor(refresh_interval=args.interval)
