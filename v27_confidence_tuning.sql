-- V27: Confidence Threshold Tuning
-- Description: Increase the minimum confidence required to open a trade to 90% for extreme precision.

UPDATE bot_params 
SET min_confidence = 90 
WHERE active = TRUE;

COMMENT ON COLUMN bot_params.min_confidence IS 'Minimum AI confidence score (0-100) required to open a position. increased to 90% for high-precision mode.';
