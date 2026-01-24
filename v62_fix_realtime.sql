-- V62: Real-time Sync Activation (FIXED SYNTAX)
-- Description: Adds core tables to the Supabase Realtime publication.
-- This ensures that the frontend receives "postgres_changes" events in real-time.

-- 1. Enable Realtime for the publication
-- We use a more compatible approach without DROP TABLE IF EXISTS which caused syntax errors.

-- Ensure the publication exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime') THEN
        CREATE PUBLICATION supabase_realtime;
    END IF;
END $$;

-- Add tables to the publication (ignoring errors if already added)
-- In Supabase, usually you just add them. If they exist, it might error but we can run them individually.
DO $$
BEGIN
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE market_signals;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE oracle_insights;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE paper_positions;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE bot_wallet;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE analytics_signals;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
END $$;

-- 2. Set REPLICA IDENTITY to FULL for more detailed updates
ALTER TABLE oracle_insights REPLICA IDENTITY FULL;
ALTER TABLE market_signals REPLICA IDENTITY FULL;
ALTER TABLE paper_positions REPLICA IDENTITY FULL;
ALTER TABLE bot_wallet REPLICA IDENTITY FULL;

COMMENT ON TABLE oracle_insights IS 'Real-time AI logic gate with Supabase Realtime enabled (V62 Fixed).';
