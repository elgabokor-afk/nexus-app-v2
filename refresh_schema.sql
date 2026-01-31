-- FORCE SCHEMA CACHE RELOAD
-- This fixes "Could not find column in schema cache" errors (PGRST204)

-- 1. Reload Config (Standard)
NOTIFY pgrst, 'reload config';

-- 2. Verify/Add 'severity' to error_logs (Idempotent)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='error_logs' AND column_name='severity') THEN
        ALTER TABLE public.error_logs ADD COLUMN severity TEXT DEFAULT 'ERROR';
    END IF;
END $$;

-- 3. Verify 'symbol' exists in signals
DO $$
BEGIN
    -- Just a check, usually it exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='signals' AND column_name='symbol') THEN
        RAISE EXCEPTION 'Column symbol missing in signals table!';
    END IF;
END $$;
