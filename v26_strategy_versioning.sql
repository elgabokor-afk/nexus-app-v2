-- V26: Strategy Versioning & Reset
-- This allows resetting/tracking performance per strategy update.

-- 1. ADD VERSION COLUMNS
ALTER TABLE bot_params ADD COLUMN IF NOT EXISTS strategy_version INT DEFAULT 1;
ALTER TABLE paper_positions ADD COLUMN IF NOT EXISTS strategy_version INT DEFAULT 1;

COMMENT ON COLUMN bot_params.strategy_version IS 'Current strategy iteration. Incrementing this effectively resets win/rate stats for the new era.';

-- 2. UPDATE STATS FUNCTION
-- Now it only calculates stats for the CURRENT strategy version.
CREATE OR REPLACE FUNCTION get_bot_stats()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    curr_version INT;
    weekly_wins INT; weekly_total INT;
    monthly_wins INT; monthly_total INT;
    yearly_wins INT; yearly_total INT;
    weekly_wr NUMERIC; monthly_wr NUMERIC; yearly_wr NUMERIC;
BEGIN
    -- Get Current Active Version
    SELECT strategy_version INTO curr_version FROM bot_params WHERE active = true LIMIT 1;
    IF curr_version IS NULL THEN curr_version := 1; END IF;

    -- Weekly (Current Version ONLY)
    SELECT COUNT(*) INTO weekly_total FROM paper_positions 
    WHERE status = 'CLOSED' AND strategy_version = curr_version AND closed_at > NOW() - INTERVAL '7 days';
    SELECT COUNT(*) INTO weekly_wins FROM paper_positions 
    WHERE status = 'CLOSED' AND strategy_version = curr_version AND closed_at > NOW() - INTERVAL '7 days' AND pnl > 0;

    -- Monthly (Current Version ONLY)
    SELECT COUNT(*) INTO monthly_total FROM paper_positions 
    WHERE status = 'CLOSED' AND strategy_version = curr_version AND closed_at > NOW() - INTERVAL '30 days';
    SELECT COUNT(*) INTO monthly_wins FROM paper_positions 
    WHERE status = 'CLOSED' AND strategy_version = curr_version AND closed_at > NOW() - INTERVAL '30 days' AND pnl > 0;

    -- Yearly (Current Version ONLY)
    SELECT COUNT(*) INTO yearly_total FROM paper_positions 
    WHERE status = 'CLOSED' AND strategy_version = curr_version AND closed_at > NOW() - INTERVAL '365 days';
    SELECT COUNT(*) INTO yearly_wins FROM paper_positions 
    WHERE status = 'CLOSED' AND strategy_version = curr_version AND closed_at > NOW() - INTERVAL '365 days' AND pnl > 0;

    -- Calculate Percentages
    IF weekly_total > 0 THEN weekly_wr := ROUND((weekly_wins::NUMERIC / weekly_total) * 100, 1); ELSE weekly_wr := 0; END IF;
    IF monthly_total > 0 THEN monthly_wr := ROUND((monthly_wins::NUMERIC / monthly_total) * 100, 1); ELSE monthly_wr := 0; END IF;
    IF yearly_total > 0 THEN yearly_wr := ROUND((yearly_wins::NUMERIC / yearly_total) * 100, 1); ELSE yearly_wr := 0; END IF;

    RETURN json_build_object(
        'strategy_version', curr_version,
        'weekly_winrate', weekly_wr,
        'weekly_trades', weekly_total,
        'monthly_winrate', monthly_wr,
        'monthly_trades', monthly_total,
        'yearly_winrate', yearly_wr,
        'yearly_trades', yearly_total
    );
END;
$$;

-- 3. INCREMENT VERSION (Reset stats for the new V25/V26 era)
UPDATE bot_params SET strategy_version = 2 WHERE active = true;
