-- Add AI Score column to Analytics Signals for Auto-Learning
-- This stores the 'Win Probability' predicted by Cosmos Engine at the time of the signal.

ALTER TABLE analytics_signals 
ADD COLUMN IF NOT EXISTS ai_score numeric DEFAULT 0.5;

COMMENT ON COLUMN analytics_signals.ai_score IS 'Cosmos AI predicted win probability (0.0 - 1.0)';
