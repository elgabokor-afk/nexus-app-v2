-- ============================================================================
-- PARTE 2: ÍNDICES PARA SISTEMA ACADÉMICO (PhD Validation)
-- Ejecutar después de PART1
-- ============================================================================

-- ACADEMIC_PAPERS
CREATE INDEX IF NOT EXISTS idx_academic_papers_university 
ON academic_papers(university, published_date DESC);

CREATE INDEX IF NOT EXISTS idx_academic_papers_citations 
ON academic_papers(citation_count DESC);

CREATE INDEX IF NOT EXISTS idx_academic_papers_tags 
ON academic_papers USING GIN(topic_tags);

-- ACADEMIC_CHUNKS (búsqueda vectorial)
-- IMPORTANTE: Requiere extensión pgvector
-- Si falla, ejecutar primero: CREATE EXTENSION IF NOT EXISTS vector;

CREATE INDEX IF NOT EXISTS idx_academic_chunks_embedding 
ON academic_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_academic_chunks_paper_id 
ON academic_chunks(paper_id);

-- Analizar tablas
ANALYZE academic_papers;
ANALYZE academic_chunks;

-- Verificar índices creados
SELECT 
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public' 
  AND (indexname LIKE 'idx_academic%')
ORDER BY tablename, indexname;
