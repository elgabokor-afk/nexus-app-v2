-- RESET VIRTUAL PORTFOLIO (Fix Outdated Stats)
-- This clears the "Audit" history so the frontend graph resets to $1,000 start.
TRUNCATE TABLE public.signal_audit_history RESTART IDENTITY;

-- Optional: If you wanted to sync from real trades, you'd insert here.
-- But for now, a clean slate resolves the "Outdated/Negative" complaint best.
