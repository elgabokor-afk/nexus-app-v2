"""
NEXUS AI - Academic Paper Cleanup Script
Removes low-quality papers from Supabase to maintain signal integrity
"""
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv('.env.local')

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Cleanup thresholds
MIN_QUALITY_SCORE = 0.60
MIN_PRESTIGE_SCORE = 0.50
STALE_DAYS = 90  # Papers older than this with 0 citations are removed

def cleanup_low_alpha_papers(dry_run: bool = True):
    """
    Remove papers that don't meet institutional standards.
    
    Criteria for removal:
    1. quality_score < 0.60
    2. prestige_score < 0.50
    3. Created > 90 days ago AND citation_count = 0 (unused)
    """
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("=" * 70)
    print("NEXUS AI - Academic Paper Cleanup")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
    print(f"Thresholds:")
    print(f"  - Min Quality Score: {MIN_QUALITY_SCORE}")
    print(f"  - Min Prestige Score: {MIN_PRESTIGE_SCORE}")
    print(f"  - Stale Period: {STALE_DAYS} days")
    print()
    
    # Calculate stale date
    stale_date = datetime.now() - timedelta(days=STALE_DAYS)
    stale_date_str = stale_date.isoformat()
    
    # Query 1: Low quality papers
    print("[1/3] Finding low quality papers...")
    try:
        low_quality = supabase.table('academic_papers')\
            .select('id, title, quality_score, university')\
            .lt('quality_score', MIN_QUALITY_SCORE)\
            .execute()
        
        low_quality_count = len(low_quality.data) if low_quality.data else 0
        print(f"   Found {low_quality_count} papers with quality_score < {MIN_QUALITY_SCORE}")
        
        if low_quality.data and not dry_run:
            ids_to_delete = [p['id'] for p in low_quality.data]
            supabase.table('academic_papers').delete().in_('id', ids_to_delete).execute()
            print(f"   ✓ Deleted {len(ids_to_delete)} low-quality papers")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Query 2: Low prestige papers
    print("\n[2/3] Finding low prestige papers...")
    try:
        low_prestige = supabase.table('academic_papers')\
            .select('id, title, prestige_score, university')\
            .lt('prestige_score', MIN_PRESTIGE_SCORE)\
            .execute()
        
        low_prestige_count = len(low_prestige.data) if low_prestige.data else 0
        print(f"   Found {low_prestige_count} papers with prestige_score < {MIN_PRESTIGE_SCORE}")
        
        if low_prestige.data and not dry_run:
            ids_to_delete = [p['id'] for p in low_prestige.data]
            supabase.table('academic_papers').delete().in_('id', ids_to_delete).execute()
            print(f"   ✓ Deleted {len(ids_to_delete)} low-prestige papers")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Query 3: Stale unused papers
    print("\n[3/3] Finding stale unused papers...")
    try:
        stale_papers = supabase.table('academic_papers')\
            .select('id, title, created_at, citation_count')\
            .lt('created_at', stale_date_str)\
            .eq('citation_count', 0)\
            .execute()
        
        stale_count = len(stale_papers.data) if stale_papers.data else 0
        print(f"   Found {stale_count} papers older than {STALE_DAYS} days with 0 citations")
        
        if stale_papers.data and not dry_run:
            ids_to_delete = [p['id'] for p in stale_papers.data]
            supabase.table('academic_papers').delete().in_('id', ids_to_delete).execute()
            print(f"   ✓ Deleted {len(ids_to_delete)} stale papers")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    total_removed = low_quality_count + low_prestige_count + stale_count
    print(f"Total papers identified for removal: {total_removed}")
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No papers were actually deleted")
        print("   Run with dry_run=False to execute cleanup")
    else:
        print("\n✓ Cleanup completed successfully")
    
    print("=" * 70)
    
    return total_removed


def get_database_stats():
    """Get current database statistics"""
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Total papers
        total = supabase.table('academic_papers').select('id', count='exact').execute()
        total_count = total.count if hasattr(total, 'count') else 0
        
        # High quality papers (>0.7)
        high_quality = supabase.table('academic_papers')\
            .select('id', count='exact')\
            .gte('quality_score', 0.7)\
            .execute()
        hq_count = high_quality.count if hasattr(high_quality, 'count') else 0
        
        # Elite papers (prestige > 1.5)
        elite = supabase.table('academic_papers')\
            .select('id', count='exact')\
            .gte('prestige_score', 1.5)\
            .execute()
        elite_count = elite.count if hasattr(elite, 'count') else 0
        
        print("\n" + "=" * 70)
        print("DATABASE STATISTICS")
        print("=" * 70)
        print(f"Total Papers: {total_count}")
        print(f"High Quality (>0.7): {hq_count} ({hq_count/total_count*100:.1f}%)" if total_count > 0 else "N/A")
        print(f"Elite Prestige (>1.5): {elite_count} ({elite_count/total_count*100:.1f}%)" if total_count > 0 else "N/A")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"ERROR getting stats: {e}")


if __name__ == "__main__":
    import sys
    
    # Check for --live flag
    is_live = '--live' in sys.argv
    
    # Show current stats
    get_database_stats()
    
    # Run cleanup
    cleanup_low_alpha_papers(dry_run=not is_live)
    
    # Show updated stats if live
    if is_live:
        print("\n" + "=" * 70)
        print("UPDATED STATISTICS")
        get_database_stats()
