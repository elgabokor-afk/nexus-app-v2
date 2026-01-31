-- Additional indexes for partially optimized tables
-- Run this after create_recommended_indexes.sql

-- ============================================
-- ÍNDICES ADICIONALES PARA user_exchanges
-- ============================================

-- Índice compuesto para la query más común: user_id + is_active
CREATE INDEX IF NOT EXISTS idx_user_exchanges_user_active 
ON public.user_exchanges USING btree (user_id, is_active)
WHERE is_active = true;

-- ============================================
-- ÍNDICES ADICIONALES PARA academic_papers
-- ============================================

-- Índice para búsqueda por universidad y fecha
CREATE INDEX IF NOT EXISTS idx_academic_papers_university_date 
ON public.academic_papers USING btree (university, published_date DESC);

-- Índice para búsqueda por citation_count (papers más citados)
CREATE INDEX IF NOT EXISTS idx_academic_papers_citations 
ON public.academic_papers USING btree (citation_count DESC);

-- Índice para búsqueda por created_at (papers recientes)
CREATE INDEX IF NOT EXISTS idx_academic_papers_created 
ON public.academic_papers USING btree (created_at DESC);

-- Índice GIN para búsqueda en topic_tags (array)
CREATE INDEX IF NOT EXISTS idx_academic_papers_topic_tags 
ON public.academic_papers USING gin (topic_tags);

-- Índices condicionales para columnas opcionales (si existen)
DO $$
BEGIN
    -- Índice para papers sin embeddings (si la columna existe)
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='academic_papers' AND column_name='embedding') THEN
        CREATE INDEX IF NOT EXISTS idx_academic_papers_no_embedding 
        ON public.academic_papers USING btree (id)
        WHERE embedding IS NULL;
    END IF;

    -- Índice para quality_score (si la columna existe)
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='academic_papers' AND column_name='quality_score') THEN
        CREATE INDEX IF NOT EXISTS idx_academic_papers_quality 
        ON public.academic_papers USING btree (quality_score DESC)
        WHERE quality_score IS NOT NULL;
    END IF;

    -- Índice para topic_cluster (si la columna existe)
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='academic_papers' AND column_name='topic_cluster') THEN
        CREATE INDEX IF NOT EXISTS idx_academic_papers_cluster 
        ON public.academic_papers USING btree (topic_cluster)
        WHERE topic_cluster IS NOT NULL;
    END IF;
END $$;

-- ============================================
-- ÍNDICES ADICIONALES PARA nexus_data_vault
-- ============================================

-- Índice compuesto para symbol + timestamp (queries de series temporales)
CREATE INDEX IF NOT EXISTS idx_nexus_vault_symbol_time 
ON public.nexus_data_vault USING btree (symbol, timestamp DESC);

-- Índice para búsqueda por source
CREATE INDEX IF NOT EXISTS idx_nexus_vault_source 
ON public.nexus_data_vault USING btree (source, timestamp DESC);

-- Índice para búsqueda por nli_score (filtrar por calidad de datos)
CREATE INDEX IF NOT EXISTS idx_nexus_vault_nli_score 
ON public.nexus_data_vault USING btree (nli_score DESC)
WHERE nli_score IS NOT NULL;

-- ============================================
-- ANALYZE para actualizar estadísticas
-- ============================================

ANALYZE public.user_exchanges;
ANALYZE public.academic_papers;
ANALYZE public.nexus_data_vault;
ANALYZE public.bot_wallet;

-- ============================================
-- RESUMEN
-- ============================================
-- user_exchanges: +1 índice compuesto (user_id + is_active)
-- academic_papers: +4 índices base (university, citations, created_at, topic_tags)
--                  +0-3 índices condicionales (embedding, quality, cluster)
-- nexus_data_vault: +3 índices (symbol+time, source, nli_score)
-- Total: 8-11 nuevos índices (dependiendo de columnas existentes)
