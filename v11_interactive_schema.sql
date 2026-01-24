-- Add closure_requested flag for manual interaction
ALTER TABLE paper_positions 
ADD COLUMN IF NOT EXISTS closure_requested boolean DEFAULT FALSE;

COMMENT ON COLUMN paper_positions.closure_requested IS 'Flag set by Frontend to request manual close by the Bot';
