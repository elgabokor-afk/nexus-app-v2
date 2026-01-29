-- MASTER SECURITY FIX: RLS Hardening & Optimization
-- Resolves ALL reported Overlaps and Performance issues across the system.

BEGIN;

-- ==========================================
-- 1. SIGNAL AUDIT HISTORY
-- ==========================================
DROP POLICY IF EXISTS "Service Write Audit" ON public.signal_audit_history;
DROP POLICY IF EXISTS "Service Insert Audit" ON public.signal_audit_history;
DROP POLICY IF EXISTS "Service Update Audit" ON public.signal_audit_history;
DROP POLICY IF EXISTS "Service Delete Audit" ON public.signal_audit_history;

CREATE POLICY "Service Insert Audit" ON public.signal_audit_history FOR INSERT WITH CHECK ((select auth.role()) = 'service_role');
CREATE POLICY "Service Update Audit" ON public.signal_audit_history FOR UPDATE USING ((select auth.role()) = 'service_role');
CREATE POLICY "Service Delete Audit" ON public.signal_audit_history FOR DELETE USING ((select auth.role()) = 'service_role');

DROP POLICY IF EXISTS "Public Read Audit" ON public.signal_audit_history;
CREATE POLICY "Public Read Audit" ON public.signal_audit_history FOR SELECT USING (true);


-- ==========================================
-- 2. ORACLE INSIGHTS
-- ==========================================
DROP POLICY IF EXISTS "Allow Oracle Insert" ON public.oracle_insights;
DROP POLICY IF EXISTS "Strict Oracle Write" ON public.oracle_insights;
CREATE POLICY "Strict Oracle Write" ON public.oracle_insights FOR INSERT TO service_role WITH CHECK (true);

DROP POLICY IF EXISTS "Allow Oracle View" ON public.oracle_insights;
DROP POLICY IF EXISTS "Public Read Access" ON public.oracle_insights;
DROP POLICY IF EXISTS "Enable read access for authenticated users" ON public.oracle_insights;
DROP POLICY IF EXISTS "Public Read Insights" ON public.oracle_insights;
CREATE POLICY "Public Read Insights" ON public.oracle_insights FOR SELECT USING (true);


-- ==========================================
-- 3. TRADE JOURNAL
-- ==========================================
DROP POLICY IF EXISTS "Users can view own journal" ON public.trade_journal;
DROP POLICY IF EXISTS "Users can insert own journal" ON public.trade_journal;
DROP POLICY IF EXISTS "Users can update own journal" ON public.trade_journal;
DROP POLICY IF EXISTS "Users can delete own journal" ON public.trade_journal;

CREATE POLICY "Users can view own journal" ON public.trade_journal FOR SELECT USING ((select auth.uid()) = user_id);
CREATE POLICY "Users can insert own journal" ON public.trade_journal FOR INSERT WITH CHECK ((select auth.uid()) = user_id);
CREATE POLICY "Users can update own journal" ON public.trade_journal FOR UPDATE USING ((select auth.uid()) = user_id);
CREATE POLICY "Users can delete own journal" ON public.trade_journal FOR DELETE USING ((select auth.uid()) = user_id);


-- ==========================================
-- 4. ACADEMIC TABLES (Papers, Chunks, Alpha)
-- ==========================================

-- 4.1 Academic Papers
DROP POLICY IF EXISTS "Service Role can manage papers" ON public.academic_papers;
DROP POLICY IF EXISTS "Service Insert Papers" ON public.academic_papers;
DROP POLICY IF EXISTS "Service Update Papers" ON public.academic_papers;
DROP POLICY IF EXISTS "Service Delete Papers" ON public.academic_papers;

CREATE POLICY "Service Insert Papers" ON public.academic_papers FOR INSERT WITH CHECK ((select auth.role()) = 'service_role');
CREATE POLICY "Service Update Papers" ON public.academic_papers FOR UPDATE USING ((select auth.role()) = 'service_role');
CREATE POLICY "Service Delete Papers" ON public.academic_papers FOR DELETE USING ((select auth.role()) = 'service_role');
-- (Read policy "Public/Bot can read papers" remains valid as FOR SELECT)

-- 4.2 Academic Chunks
DROP POLICY IF EXISTS "Service Role can manage chunks" ON public.academic_chunks;
DROP POLICY IF EXISTS "Service Insert Chunks" ON public.academic_chunks;
DROP POLICY IF EXISTS "Service Update Chunks" ON public.academic_chunks;
DROP POLICY IF EXISTS "Service Delete Chunks" ON public.academic_chunks;

CREATE POLICY "Service Insert Chunks" ON public.academic_chunks FOR INSERT WITH CHECK ((select auth.role()) = 'service_role');
CREATE POLICY "Service Update Chunks" ON public.academic_chunks FOR UPDATE USING ((select auth.role()) = 'service_role');
CREATE POLICY "Service Delete Chunks" ON public.academic_chunks FOR DELETE USING ((select auth.role()) = 'service_role');
-- (Read policy "Public/Bot can read chunks" remains valid as FOR SELECT)

-- 4.3 Academic Alpha
DROP POLICY IF EXISTS "Service Role can manage alpha" ON public.academic_alpha;
DROP POLICY IF EXISTS "Service Insert Alpha" ON public.academic_alpha;
DROP POLICY IF EXISTS "Service Update Alpha" ON public.academic_alpha;
DROP POLICY IF EXISTS "Service Delete Alpha" ON public.academic_alpha;

CREATE POLICY "Service Insert Alpha" ON public.academic_alpha FOR INSERT WITH CHECK ((select auth.role()) = 'service_role');
CREATE POLICY "Service Update Alpha" ON public.academic_alpha FOR UPDATE USING ((select auth.role()) = 'service_role');
CREATE POLICY "Service Delete Alpha" ON public.academic_alpha FOR DELETE USING ((select auth.role()) = 'service_role');

-- ==========================================
-- 5. SIGNALS & TRADES (Core System)
-- ==========================================
DROP POLICY IF EXISTS "Public Read Signals" ON public.signals;
DROP POLICY IF EXISTS "Service Role Write Signals" ON public.signals;
CREATE POLICY "Public Read Signals" ON public.signals FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Service Role Write Signals" ON public.signals FOR ALL TO service_role USING (true);

DROP POLICY IF EXISTS "Public Read Trades" ON public.paper_trades;
DROP POLICY IF EXISTS "Service Role Write Trades" ON public.paper_trades;
CREATE POLICY "Public Read Trades" ON public.paper_trades FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Service Role Write Trades" ON public.paper_trades FOR ALL TO service_role USING (true);

DROP POLICY IF EXISTS "Universal Dashboard Access" ON public.paper_positions;
DROP POLICY IF EXISTS "Public Read Positions" ON public.paper_positions;
DROP POLICY IF EXISTS "Service Role Write Positions" ON public.paper_positions;
CREATE POLICY "Public Read Positions" ON public.paper_positions FOR SELECT TO anon, authenticated USING (true);
CREATE POLICY "Service Role Write Positions" ON public.paper_positions FOR ALL TO service_role USING (true);

-- ==========================================
-- 6. ANALYTICS (Helper Table)
-- ==========================================
-- Used for AI Heatmaps provided the table exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename  = 'analytics_signals') THEN
        ALTER TABLE public.analytics_signals ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS "Public Read Analytics" ON public.analytics_signals;
        CREATE POLICY "Public Read Analytics" ON public.analytics_signals FOR SELECT TO anon, authenticated USING (true);
        
        DROP POLICY IF EXISTS "Service Write Analytics" ON public.analytics_signals;
        CREATE POLICY "Service Write Analytics" ON public.analytics_signals FOR ALL TO service_role USING (true);
    END IF;
END $$;

COMMIT;
