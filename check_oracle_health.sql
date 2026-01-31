-- check_oracle_health.sql
-- 1. Check most recent Oracle Insight (BLM Thoughts)
SELECT * FROM public.oracle_insights ORDER BY timestamp DESC LIMIT 5;

-- 2. Check Neural Link Status (Model Registry)
SELECT * FROM public.ai_model_registry ORDER BY last_bootstrap_at DESC LIMIT 5;

-- 3. Check for specific errors in error_logs related to Oracle
SELECT * FROM public.error_logs WHERE message LIKE '%Oracle%' OR service = 'cosmos_brain' ORDER BY created_at DESC LIMIT 5;
