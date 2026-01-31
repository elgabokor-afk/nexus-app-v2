-- Performance Fix: Optimize RLS policy for signal_audit_history
-- Problem: auth.role() was being called for every row, causing slowdowns.
-- Solution: Wrap in (select auth.role()) to allow Postgres to cache the result per statement.

BEGIN;

-- 1. Drop the inefficient policy
DROP POLICY IF EXISTS "Service Write Audit" ON public.signal_audit_history;

-- 2. Create the optimized policy
CREATE POLICY "Service Write Audit"
    ON public.signal_audit_history FOR ALL
    USING ((select auth.role()) = 'service_role');

COMMIT;
