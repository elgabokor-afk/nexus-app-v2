-- V2001: EMERGENCY SPACE RESCUE (Corrected)
-- Fixes "column timestamp does not exist" error.

-- 1. Aggressive Log Cleanup (Using 'created_at' which is standard)
-- Try specific 'created_at' for logs
DELETE FROM error_logs 
WHERE created_at < NOW() - INTERVAL '24 hours';

-- 2. Clean High-Frequency Indicators (Keep signals, using 'timestamp' as verified)
DELETE FROM market_signals 
WHERE timestamp < NOW() - INTERVAL '3 days';

-- 3. Analytics Noise
DELETE FROM analytics_signals 
WHERE created_at < NOW() - INTERVAL '3 days';

-- 4. Verify
select count(*) as "Remaining Errors" from error_logs;
select count(*) as "Remaining Signals" from market_signals;
