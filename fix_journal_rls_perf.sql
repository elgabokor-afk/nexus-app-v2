-- Performance Fix: Optimize RLS policies for trade_journal
-- Problem: auth.uid() was being called for every row, causing slowdowns.
-- Solution: Wrap in (select auth.uid()) to allow Postgres to cache the result per statement.

BEGIN;

-- 1. Drop the inefficient policies
DROP POLICY IF EXISTS "Users can view own journal" ON public.trade_journal;
DROP POLICY IF EXISTS "Users can insert own journal" ON public.trade_journal;
DROP POLICY IF EXISTS "Users can update own journal" ON public.trade_journal;
DROP POLICY IF EXISTS "Users can delete own journal" ON public.trade_journal;

-- 2. Create the optimized policies
CREATE POLICY "Users can view own journal" 
    ON public.trade_journal FOR SELECT 
    USING ((select auth.uid()) = user_id);

CREATE POLICY "Users can insert own journal" 
    ON public.trade_journal FOR INSERT 
    WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "Users can update own journal" 
    ON public.trade_journal FOR UPDATE 
    USING ((select auth.uid()) = user_id);

CREATE POLICY "Users can delete own journal" 
    ON public.trade_journal FOR DELETE 
    USING ((select auth.uid()) = user_id);

COMMIT;
