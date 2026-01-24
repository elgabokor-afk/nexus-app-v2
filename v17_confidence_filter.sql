-- Add Minimum Confidence Threshold
ALTER TABLE bot_params 
ADD COLUMN IF NOT EXISTS min_confidence numeric DEFAULT 75;

COMMENT ON COLUMN bot_params.min_confidence IS 'Minimum AI Confidence Score (0-100) required to take a trade';

-- Reset defaults
UPDATE bot_params SET min_confidence = 75 WHERE active = TRUE;
