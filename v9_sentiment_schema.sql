ALTER TABLE analytics_signals 
ADD COLUMN IF NOT EXISTS sentiment_score numeric DEFAULT 50;

COMMENT ON COLUMN analytics_signals.sentiment_score IS 'Fear & Greed Index (0-100)';
