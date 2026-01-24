CREATE OR REPLACE FUNCTION get_bot_stats()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    weekly_wins INT;
    weekly_total INT;
    monthly_wins INT;
    monthly_total INT;
    yearly_wins INT;
    yearly_total INT;
    
    weekly_wr NUMERIC;
    monthly_wr NUMERIC;
    yearly_wr NUMERIC;
BEGIN
    -- Weekly (7 Days)
    SELECT COUNT(*) INTO weekly_total FROM paper_positions 
    WHERE status = 'CLOSED' AND closed_at > NOW() - INTERVAL '7 days';
    
    SELECT COUNT(*) INTO weekly_wins FROM paper_positions 
    WHERE status = 'CLOSED' AND closed_at > NOW() - INTERVAL '7 days' AND pnl > 0;

    -- Monthly (30 Days)
    SELECT COUNT(*) INTO monthly_total FROM paper_positions 
    WHERE status = 'CLOSED' AND closed_at > NOW() - INTERVAL '30 days';
    
    SELECT COUNT(*) INTO monthly_wins FROM paper_positions 
    WHERE status = 'CLOSED' AND closed_at > NOW() - INTERVAL '30 days' AND pnl > 0;

    -- Yearly (365 Days)
    SELECT COUNT(*) INTO yearly_total FROM paper_positions 
    WHERE status = 'CLOSED' AND closed_at > NOW() - INTERVAL '365 days';
    
    SELECT COUNT(*) INTO yearly_wins FROM paper_positions 
    WHERE status = 'CLOSED' AND closed_at > NOW() - INTERVAL '365 days' AND pnl > 0;

    -- Calculate Percentages (Handle Division by Zero)
    IF weekly_total > 0 THEN weekly_wr := ROUND((weekly_wins::NUMERIC / weekly_total) * 100, 1); ELSE weekly_wr := 0; END IF;
    IF monthly_total > 0 THEN monthly_wr := ROUND((monthly_wins::NUMERIC / monthly_total) * 100, 1); ELSE monthly_wr := 0; END IF;
    IF yearly_total > 0 THEN yearly_wr := ROUND((yearly_wins::NUMERIC / yearly_total) * 100, 1); ELSE yearly_wr := 0; END IF;

    RETURN json_build_object(
        'weekly_winrate', weekly_wr,
        'weekly_trades', weekly_total,
        'monthly_winrate', monthly_wr,
        'monthly_trades', monthly_total,
        'yearly_winrate', yearly_wr,
        'yearly_trades', yearly_total
    );
END;
$$;
