-- Add dynamic risk percentage per trade
ALTER TABLE bot_params 
ADD COLUMN IF NOT EXISTS account_risk_pct numeric DEFAULT 0.02; -- Default 2% risk per trade

COMMENT ON COLUMN bot_params.account_risk_pct IS 'Percentage of Equity to risk per trade (e.g. 0.02 = 2%)';

-- Reset to safe default
UPDATE bot_params SET account_risk_pct = 0.02 WHERE active = TRUE;
