-- Diagnostic: Check Audit vs Trades
SELECT 'signal_audit_history' as source, count(*) as count, sum(pnl_percent) as total_pnl_pct FROM public.signal_audit_history
UNION ALL
SELECT 'paper_trades' as source, count(*) as count, sum(realized_pnl) as total_pnl FROM public.paper_trades WHERE bot_status = 'CLOSED';

-- View recent audit logs
SELECT * FROM public.signal_audit_history ORDER BY created_at DESC LIMIT 5;
-- View recent trades
SELECT * FROM public.paper_trades ORDER BY created_at DESC LIMIT 5;
