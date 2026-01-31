-- ============================================================================
-- NEXUS AI - DATABASE SETUP (FIXED VERSION)
-- ============================================================================
-- Compatible with existing academic_papers schema
-- Run this in Supabase SQL Editor
-- ============================================================================

-- 1. ENABLE EXTENSIONS
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- 2. CHECK EXISTING SCHEMA
-- First, let's see what columns exist in academic_papers
DO $$ 
BEGIN
    RAISE NOTICE 'Checking academic_papers schema...';
END $$;

-- 3. ADD MISSING COLUMNS TO academic_papers (if they don't exist)
DO $$ 
BEGIN
    -- Add embedding column if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='academic_papers' AND column_name='embedding'
    ) THEN
        ALTER TABLE academic_papers ADD COLUMN embedding vector(1536);
        RAISE NOTICE 'Added embedding column';
    END IF;

    -- Add metadata columns if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='academic_papers' AND column_name='embedding_model') THEN
        ALTER TABLE academic_papers ADD COLUMN embedding_model TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='academic_papers' AND column_name='embedding_generated_at') THEN
        ALTER TABLE academic_papers ADD COLUMN embedding_generated_at TIMESTAMPTZ;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='academic_papers' AND column_name='topic_cluster') THEN
        ALTER TABLE academic_papers ADD COLUMN topic_cluster INT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='academic_papers' AND column_name='keywords') THEN
        ALTER TABLE academic_papers ADD COLUMN keywords TEXT[];
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='academic_papers' AND column_name='citation_count') THEN
        ALTER TABLE academic_papers ADD COLUMN citation_count INT DEFAULT 0;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='academic_papers' AND column_name='quality_score') THEN
        ALTER TABLE academic_papers ADD COLUMN quality_score FLOAT DEFAULT 0.5;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='academic_papers' AND column_name='is_validated') THEN
        ALTER TABLE academic_papers ADD COLUMN is_validated BOOLEAN DEFAULT false;
    END IF;
END $$;

-- 4. CREATE PAPER CLUSTERS TABLE
CREATE TABLE IF NOT EXISTS paper_clusters (
    cluster_id INT PRIMARY KEY,
    topic_name TEXT NOT NULL,
    description TEXT,
    paper_count INT DEFAULT 0,
    sample_papers TEXT[],
    keywords TEXT[],
    avg_quality_score FLOAT DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. CREATE SEARCH HISTORY TABLE
CREATE TABLE IF NOT EXISTS paper_search_history (
    id BIGSERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    results_count INT,
    avg_similarity FLOAT,
    search_type TEXT DEFAULT 'semantic',
    user_id UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. CREATE PAPER CITATIONS TABLE
CREATE TABLE IF NOT EXISTS paper_citations (
    id BIGSERIAL PRIMARY KEY,
    signal_id BIGINT,
    paper_id BIGINT REFERENCES academic_papers(id),
    similarity_score FLOAT,
    confidence_boost FLOAT,
    cited_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(signal_id, paper_id)
);

-- 7. CREATE INDEXES
CREATE INDEX IF NOT EXISTS idx_papers_embedding 
ON academic_papers USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_papers_cluster ON academic_papers(topic_cluster);
CREATE INDEX IF NOT EXISTS idx_papers_quality ON academic_papers(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_papers_validated ON academic_papers(is_validated) WHERE is_validated = true;

-- 8. CREATE SEMANTIC SEARCH FUNCTION
CREATE OR REPLACE FUNCTION match_papers(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.70,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id bigint,
    paper_id text,
    authors text,
    university text,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        ap.id,
        ap.paper_id,
        ap.authors,
        ap.university,
        1 - (ap.embedding <=> query_embedding) as similarity
    FROM academic_papers ap
    WHERE ap.embedding IS NOT NULL
        AND 1 - (ap.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC, quality_score DESC
    LIMIT match_count;
$$;

-- 9. CREATE HELPER FUNCTIONS
CREATE OR REPLACE FUNCTION get_similar_papers(
    paper_id_param bigint,
    similarity_threshold float DEFAULT 0.75,
    limit_count int DEFAULT 5
)
RETURNS TABLE (
    id bigint,
    paper_id text,
    authors text,
    university text,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        ap2.id,
        ap2.paper_id,
        ap2.authors,
        ap2.university,
        1 - (ap1.embedding <=> ap2.embedding) as similarity
    FROM academic_papers ap1
    CROSS JOIN academic_papers ap2
    WHERE ap1.id = paper_id_param
        AND ap2.id != paper_id_param
        AND ap1.embedding IS NOT NULL
        AND ap2.embedding IS NOT NULL
        AND 1 - (ap1.embedding <=> ap2.embedding) > similarity_threshold
    ORDER BY similarity DESC
    LIMIT limit_count;
$$;

-- 10. CREATE STATS VIEW
CREATE OR REPLACE VIEW paper_stats AS
SELECT
    COUNT(*) as total_papers,
    COUNT(embedding) as papers_with_embeddings,
    COUNT(*) - COUNT(embedding) as papers_missing_embeddings,
    COUNT(DISTINCT university) as unique_universities,
    COUNT(DISTINCT topic_cluster) as unique_clusters,
    AVG(quality_score) as avg_quality_score,
    COUNT(*) FILTER (WHERE is_validated = true) as validated_papers
FROM academic_papers;

-- 11. CREATE UNIVERSITY STATS VIEW
CREATE OR REPLACE VIEW university_stats AS
SELECT
    university,
    COUNT(*) as paper_count,
    COUNT(embedding) as embedded_count,
    AVG(citation_count)::int as avg_citations,
    AVG(quality_score) as avg_quality
FROM academic_papers
WHERE university IS NOT NULL
GROUP BY university
ORDER BY paper_count DESC;

-- 12. ROW LEVEL SECURITY
ALTER TABLE academic_papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_clusters ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_citations ENABLE ROW LEVEL SECURITY;

-- Public read access
DROP POLICY IF EXISTS "Public read papers" ON academic_papers;
CREATE POLICY "Public read papers" ON academic_papers
    FOR SELECT TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "Service role all papers" ON academic_papers;
CREATE POLICY "Service role all papers" ON academic_papers
    FOR ALL TO service_role
    USING (true);

DROP POLICY IF EXISTS "Public read clusters" ON paper_clusters;
CREATE POLICY "Public read clusters" ON paper_clusters
    FOR SELECT TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "Service role all clusters" ON paper_clusters;
CREATE POLICY "Service role all clusters" ON paper_clusters
    FOR ALL TO service_role
    USING (true);

-- 13. GRANT PERMISSIONS
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON academic_papers TO anon, authenticated;
GRANT SELECT ON paper_clusters TO anon, authenticated;
GRANT SELECT ON paper_stats TO anon, authenticated;
GRANT SELECT ON university_stats TO anon, authenticated;

-- 14. VERIFICATION
SELECT 'Setup complete!' as status,
       NOW() as completed_at;

-- Check what was created
SELECT 'Extensions' as category, COUNT(*) as count 
FROM pg_extension 
WHERE extname IN ('vector', 'pg_trgm', 'btree_gin')
UNION ALL
SELECT 'Tables', COUNT(*) 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('academic_papers', 'paper_clusters', 'paper_search_history', 'paper_citations')
UNION ALL
SELECT 'Functions', COUNT(*) 
FROM information_schema.routines 
WHERE routine_schema = 'public' 
AND routine_name IN ('match_papers', 'get_similar_papers')
UNION ALL
SELECT 'Views', COUNT(*) 
FROM information_schema.views 
WHERE table_schema = 'public' 
AND table_name IN ('paper_stats', 'university_stats');

-- Show current stats
SELECT * FROM paper_stats;
