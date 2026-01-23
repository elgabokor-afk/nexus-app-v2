-- SECURE DATABASE PERMISSIONS
-- Run this in Supabase SQL Editor to fix the security warning

-- 1. Revoke WRITE permissions from public (anon) and logged in users (authenticated)
-- We only want the Dashboard to READ, not write.
REVOKE INSERT, UPDATE, DELETE ON public.market_signals FROM anon, authenticated;
REVOKE INSERT, UPDATE, DELETE ON public.market_sentiment FROM anon, authenticated;

-- 2. Drop the insecure "Service Role Write" policies
-- (Service Role bypasses RLS automatically, so we don't need a policy allowing it with 'true')
DROP POLICY IF EXISTS "Service Role Write Signals" ON public.market_signals;
DROP POLICY IF EXISTS "Service Role Write Sentiment" ON public.market_sentiment;

-- 3. Ensure Public Read is still allowed (For the Dashboard)
-- This is safe because it is SELECT only.
-- (Existing "Public Read Signals" policy is fine)

-- 4. Verify
-- anon/authenticated should only have SELECT
GRANT SELECT ON public.market_signals TO anon, authenticated;
GRANT SELECT ON public.market_sentiment TO anon, authenticated;
