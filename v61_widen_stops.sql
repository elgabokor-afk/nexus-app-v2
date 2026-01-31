-- V61: Stop Loss Widening (Correction Tolerance)
-- Description: Increase the default Stop Loss multiplier to allow for market corrections.

UPDATE bot_params 
SET stop_loss_atr_mult = 2.5 
WHERE active = TRUE;

COMMENT ON COLUMN bot_params.stop_loss_atr_mult IS 'ATR multiplier for Stop Loss. Increased to 2.5 in V61 for correction tolerance.';
