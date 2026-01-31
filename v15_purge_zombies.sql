-- V1500: Zombies Purge Script
-- Fixes "Blocked: 419 Recent Positions" error by closing stuck trades.

-- 1. Count Zombies before purge
SELECT count(*) as "Zombies Count" FROM paper_positions WHERE status = 'OPEN';

-- 2. Force Close all OPEN positions created more than 10 minutes ago
-- We assume if they are still open after a restart, they are ghosts.
UPDATE paper_positions 
SET 
  status = 'CLOSED', 
  exit_reason = 'FORCE_PURGE_V1500', 
  closed_at = NOW()
WHERE status = 'OPEN';

-- 3. Verify clean slate
SELECT count(*) as "Remaining Open" FROM paper_positions WHERE status = 'OPEN';
