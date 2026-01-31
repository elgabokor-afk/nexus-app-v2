-- RLS Optimization: Remove overlapping SELECT policies
-- Problem: 'Service Write Audit' was FOR ALL, which includes SELECT.
-- But 'Public Read Audit' already allows SELECT for everyone.
-- This caused double evaluation for service_role during reads.

BEGIN;

-- 1. Drop old combined policy
DROP POLICY IF EXISTS "Service Write Audit" ON public.signal_audit_history;

-- 2. Create specific write policies (INSERT, UPDATE, DELETE)
-- Exclude SELECT because "Public Read Audit" handles it globally.

CREATE POLICY "Service Insert Audit"
    ON public.signal_audit_history FOR INSERT
    WITH CHECK ((select auth.role()) = 'service_role');

CREATE POLICY "Service Update Audit"
    ON public.signal_audit_history FOR UPDATE
    USING ((select auth.role()) = 'service_role');

CREATE POLICY "Service Delete Audit"
    ON public.signal_audit_history FOR DELETE
    USING ((select auth.role()) = 'service_role');

COMMIT;
