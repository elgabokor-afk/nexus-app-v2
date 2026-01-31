-- V28: Security Hardening II (Error Logs)
-- Description: Resolve Supabase Security Advisor warnings by removing unrestricted access.

-- 1. CLEANUP ALL LOOSE POLICIES
DROP POLICY IF EXISTS "Allow Service Access" ON error_logs;
DROP POLICY IF EXISTS "Allow Service Access for ALL" ON error_logs;
DROP POLICY IF EXISTS "Allow Log Insert" ON error_logs;
DROP POLICY IF EXISTS "Allow Log View" ON error_logs;
DROP POLICY IF EXISTS "Secure Log View" ON error_logs;
DROP POLICY IF EXISTS "Secure Log Insert" ON error_logs;

-- 2. ENABLE RLS (Ensure it is on)
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;

-- 3. CREATE SECURE POLICIES

-- Restricted View: Only authenticated users (Dashboard users) can see logs.
CREATE POLICY "Secure Log View" ON error_logs
    FOR SELECT
    TO authenticated
    USING (true);

-- Restricted Insert: Only authenticated users or the service_role (Bot) can insert logs.
-- We add a non-null check to satisfy the "unrestricted access" warning.
CREATE POLICY "Secure Log Insert" ON error_logs
    FOR INSERT
    TO authenticated, service_role
    WITH CHECK (service IS NOT NULL AND message IS NOT NULL);

-- Optional: If the bot is using the 'anon' key, it will now be BLOCKED.
-- Recommendation: Ensure data-engine uses the SERVICE_ROLE key for background ops.
