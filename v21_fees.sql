-- V21: Trading Fees Implementation
-- Add trading_fee_pct to bot_params
ALTER TABLE bot_params 
ADD COLUMN IF NOT EXISTS trading_fee_pct NUMERIC DEFAULT 0.0005;

COMMENT ON COLUMN bot_params.trading_fee_pct IS 'Trading Fee percentage (e.g. 0.0005 for 0.05% per leg, 0.1% RT)';

-- Update active params
UPDATE bot_params SET trading_fee_pct = 0.0005 WHERE active = TRUE;
