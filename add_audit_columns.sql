-- Add Audit Columns for Cosmos AI Live Management
-- Allows the AI to "Tag" signals with updates like "Volume Dropping -> Tightened TP"

ALTER TABLE public.signals 
ADD COLUMN IF NOT EXISTS audit_note TEXT,
ADD COLUMN IF NOT EXISTS last_audit_ts TIMESTAMPTZ;

-- Add index for faster querying of active signals to audit
CREATE INDEX IF NOT EXISTS idx_signals_status_active ON public.signals(status) WHERE status = 'ACTIVE';
