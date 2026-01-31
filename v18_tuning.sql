-- V18 Tuning: User Requested Parameters
-- Leverage: 4x
-- Max Positions: 5
-- Min Confidence: 78%

UPDATE bot_params 
SET 
    max_open_positions = 5,
    default_leverage = 4,
    min_confidence = 78
WHERE active = TRUE;

-- Verify changes
SELECT * FROM bot_params WHERE active = TRUE;
