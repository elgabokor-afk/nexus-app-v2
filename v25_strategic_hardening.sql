-- V25: Strategic Hardening Parameters
-- Enhance trade selection quality vs quantity.

ALTER TABLE bot_params 
ADD COLUMN IF NOT EXISTS min_rrr NUMERIC DEFAULT 1.5,
ADD COLUMN IF NOT EXISTS min_net_profit_pct NUMERIC DEFAULT 1.0;

COMMENT ON COLUMN bot_params.min_rrr IS 'Minimum Risk/Reward Ratio required to take a trade';
COMMENT ON COLUMN bot_params.min_net_profit_pct IS 'Minimum Net Profit (after fees) % of margin required to take a trade';

-- Update active configurations
UPDATE bot_params 
SET 
    min_rrr = 1.5, 
    min_net_profit_pct = 1.0,
    min_confidence = 80 -- Even stricter by default now
WHERE active = TRUE;
