-- V30: Strategic Version Upgrade
-- Description: Increment strategy version to v3 to reset stats for the new Trend Alignment + Net-Targeted TP/SL engine.

UPDATE bot_params 
SET strategy_version = 3 
WHERE active = TRUE;

COMMENT ON COLUMN bot_params.strategy_version IS 'Current strategy iteration. v3 = Trend Alignment + Net-Targeted TP/SL math.';
