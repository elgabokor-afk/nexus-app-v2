-- Add Risk Management columns to bot_params
ALTER TABLE bot_params 
ADD COLUMN IF NOT EXISTS max_open_positions INTEGER DEFAULT 3,
ADD COLUMN IF NOT EXISTS cooldown_minutes INTEGER DEFAULT 15;

COMMENT ON COLUMN bot_params.max_open_positions IS 'Maximum number of concurrent open positions allowed';
COMMENT ON COLUMN bot_params.cooldown_minutes IS 'Minimum minutes between opening new positions';

-- Update existing default row if it exists
UPDATE bot_params 
SET max_open_positions = 3, cooldown_minutes = 15 
WHERE active = TRUE;
