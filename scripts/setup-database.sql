-- ============================================================================
-- NEXUS AI TRADING PLATFORM - DATABASE SETUP
-- ============================================================================
-- Ejecutar en Supabase SQL Editor
-- Este script prepara la base de datos para el sistema RAG con 1000+ papers
-- ============================================================================

-- 1. ENABLE EXTENSIONS
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS btree_gin;  -- For composite indexes

-- 2. UPDATE ACADEMIC_PAPERS TABLE
DO $$ 
BEGIN
    -- Add embedding column if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='academic_papers' AND column_name='embedding'
    ) THEN
        ALTER TABLE academic_papers ADD COLUMN embedding vector(1536);
    END IF;

    -- Add metadata columns
    ALTER TABLE academic_papers ADD COLUMN IF NOT EXISTS embedding_model TEXT;
    ALTER TABLE academic_papers ADD COLUMN IF NOT EXISTS embedding_generated_at TIMESTAMPTZ;
    ALTER TABLE academic_papers ADD COLUMN IF NOT EXISTS topic_cluster INT;
    ALTER TABLE academic_papers ADD COLUMN IF NOT EXISTS keywords TEXT[];
    ALTER TABLE academic_papers ADD COLUMN IF NOT EXISTS citation_count INT DEFAULT 0;
    ALTER TABLE academic_papers ADD COLUMN IF NOT EXISTS content_tsv tsvector;
    ALTER TABLE academic_papers ADD COLUMN IF NOT EXISTS quality_score FLOAT DEFAULT 0.5;
    ALTER TABLE academic_papers ADD COLUMN IF NOT EXISTS is_validated BOOLEAN DEFAULT false;
END $$;

-- 3. CREATE PAPER CLUSTERS TABLE
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

-- 4. CREATE SEARCH HISTORY TABLE
CREATE TABLE IF NOT EXISTS paper_search_history (
    id BIGSERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    results_count INT,
    avg_similarity FLOAT,
    search_type TEXT DEFAULT 'semantic',  -- semantic, fulltext, hybrid
    user_id UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. CREATE PAPER CITATIONS TABLE
CREATE TABLE IF NOT EXISTS paper_citations (
    id BIGSERIAL PRIMARY KEY,
    signal_id BIGINT REFERENCES signals(id),
    paper_id BIGINT REFERENCES academic_papers(id),
    similarity_score FLOAT,
    confidence_boost FLOAT,
    cited_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(signal_id, paper_id)
);

-- 6. CREATE INDEXES
CREATE INDEX IF NOT EXISTS idx_papers_embedding 
ON academic_papers USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_papers_cluster ON academic_papers(topic_cluster);
CREATE INDEX IF NOT EXISTS idx_papers_university ON academic_papers(university);
CREATE INDEX IF NOT EXISTS idx_papers_created ON academic_papers(created_at);
CREATE INDEX IF NOT EXISTS idx_papers_keywords ON academic_papers USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_papers_quality ON academic_papers(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_papers_validated ON academic_papers(is_validated) WHERE is_validated = true;

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_papers_fts ON academic_papers USING GIN(content_tsv);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_papers_cluster_quality 
ON academic_papers(topic_cluster, quality_score DESC);

CREATE INDEX IF NOT EXISTS idx_papers_university_validated 
ON academic_papers(university, is_validated);

-- 7. UPDATE TSVECTOR COLUMN
UPDATE academic_papers 
SET content_tsv = to_tsvector('english', coalesce(content, '') || ' ' || coalesce(authors, ''))
WHERE content_tsv IS NULL;

-- 8. CREATE TRIGGER FOR TSVECTOR AUTO-UPDATE
CREATE OR REPLACE FUNCTION papers_tsvector_trigger() RETURNS trigger AS $$
BEGIN
    NEW.content_tsv := to_tsvector('english', coalesce(NEW.content, '') || ' ' || coalesce(NEW.authors, ''));
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tsvector_update ON academic_papers;
CREATE TRIGGER tsvector_update BEFORE INSERT OR UPDATE ON academic_papers
FOR EACH ROW EXECUTE FUNCTION papers_tsvector_trigger();

-- 9. CREATE SEMANTIC SEARCH FUNCTION
CREATE OR REPLACE FUNCTION match_papers(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.70,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id bigint,
    paper_id text,
    content text,
    authors text,
    university text,
    pdf_url text,
    topic_cluster int,
    citation_count int,
    quality_score float,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        ap.id,
        ap.paper_id,
        ap.content,
        ap.authors,
        ap.university,
        ap.pdf_url,
        ap.topic_cluster,
        ap.citation_count,
        ap.quality_score,
        1 - (ap.embedding <=> query_embedding) as similarity
    FROM academic_papers ap
    WHERE ap.embedding IS NOT NULL
        AND 1 - (ap.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC, quality_score DESC
    LIMIT match_count;
$$;

-- 10. CREATE HYBRID SEARCH FUNCTION
CREATE OR REPLACE FUNCTION hybrid_search_papers(
    query_text text,
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.65,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id bigint,
    paper_id text,
    content text,
    authors text,
    university text,
    similarity float,
    text_rank float,
    combined_score float
)
LANGUAGE sql STABLE
AS $$
    WITH semantic_search AS (
        SELECT
            ap.id,
            1 - (ap.embedding <=> query_embedding) as similarity
        FROM academic_papers ap
        WHERE ap.embedding IS NOT NULL
    ),
    text_search AS (
        SELECT
            ap.id,
            ts_rank(ap.content_tsv, plainto_tsquery('english', query_text)) as text_rank
        FROM academic_papers ap
        WHERE ap.content_tsv @@ plainto_tsquery('english', query_text)
    )
    SELECT
        ap.id,
        ap.paper_id,
        ap.content,
        ap.authors,
        ap.university,
        COALESCE(ss.similarity, 0) as similarity,
        COALESCE(ts.text_rank, 0) as text_rank,
        (COALESCE(ss.similarity, 0) * 0.7 + COALESCE(ts.text_rank, 0) * 0.3) as combined_score
    FROM academic_papers ap
    LEFT JOIN semantic_search ss ON ap.id = ss.id
    LEFT JOIN text_search ts ON ap.id = ts.id
    WHERE (ss.similarity > match_threshold OR ts.text_rank > 0)
    ORDER BY combined_score DESC
    LIMIT match_count;
$$;

-- 11. CREATE HELPER FUNCTIONS
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

CREATE OR REPLACE FUNCTION update_cluster_stats()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE paper_clusters pc
    SET 
        paper_count = (
            SELECT COUNT(*) 
            FROM academic_papers ap 
            WHERE ap.topic_cluster = pc.cluster_id
        ),
        avg_quality_score = (
            SELECT AVG(quality_score)
            FROM academic_papers ap
            WHERE ap.topic_cluster = pc.cluster_id
        ),
        updated_at = NOW();
END;
$$;

-- 12. CREATE VIEWS
CREATE OR REPLACE VIEW paper_stats AS
SELECT
    COUNT(*) as total_papers,
    COUNT(embedding) as papers_with_embeddings,
    COUNT(*) - COUNT(embedding) as papers_missing_embeddings,
    COUNT(DISTINCT university) as unique_universities,
    COUNT(DISTINCT topic_cluster) as unique_clusters,
    AVG(LENGTH(content))::int as avg_content_length,
    AVG(quality_score) as avg_quality_score,
    COUNT(*) FILTER (WHERE is_validated = true) as validated_papers
FROM academic_papers;

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

CREATE OR REPLACE VIEW cluster_stats AS
SELECT
    pc.cluster_id,
    pc.topic_name,
    pc.description,
    COUNT(ap.id) as paper_count,
    AVG(ap.citation_count)::int as avg_citations,
    AVG(ap.quality_score) as avg_quality
FROM paper_clusters pc
LEFT JOIN academic_papers ap ON ap.topic_cluster = pc.cluster_id
GROUP BY pc.cluster_id, pc.topic_name, pc.description
ORDER BY paper_count DESC;

CREATE OR REPLACE VIEW top_cited_papers AS
SELECT
    id,
    paper_id,
    authors,
    university,
    citation_count,
    quality_score,
    topic_cluster
FROM academic_papers
WHERE citation_count > 0
ORDER BY citation_count DESC, quality_score DESC
LIMIT 100;

-- 13. ROW LEVEL SECURITY
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

DROP POLICY IF EXISTS "Users read own history" ON paper_search_history;
CREATE POLICY "Users read own history" ON paper_search_history
    FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role all history" ON paper_search_history;
CREATE POLICY "Service role all history" ON paper_search_history
    FOR ALL TO service_role
    USING (true);

-- 14. GRANT PERMISSIONS
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON academic_papers TO anon, authenticated;
GRANT SELECT ON paper_clusters TO anon, authenticated;
GRANT SELECT ON paper_stats TO anon, authenticated;
GRANT SELECT ON university_stats TO anon, authenticated;
GRANT SELECT ON cluster_stats TO anon, authenticated;
GRANT SELECT ON top_cited_papers TO anon, authenticated;

-- 15. CREATE AUDIT LOG
CREATE TABLE IF NOT EXISTS paper_audit_log (
    id BIGSERIAL PRIMARY KEY,
    paper_id BIGINT REFERENCES academic_papers(id),
    action TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_paper ON paper_audit_log(paper_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON paper_audit_log(created_at);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check extensions
SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'pg_trgm', 'btree_gin');

-- Check tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('academic_papers', 'paper_clusters', 'paper_search_history', 'paper_citations')
ORDER BY table_name;

-- Check indexes
SELECT indexname FROM pg_indexes 
WHERE tablename = 'academic_papers' 
ORDER BY indexname;

-- Check functions
SELECT routine_name FROM information_schema.routines 
WHERE routine_schema = 'public' 
AND routine_name IN ('match_papers', 'hybrid_search_papers', 'get_similar_papers')
ORDER BY routine_name;

-- Get stats
SELECT * FROM paper_stats;

-- ============================================================================
-- SETUP COMPLETE
-- ============================================================================
SELECT 'Database setup complete!' as status;
