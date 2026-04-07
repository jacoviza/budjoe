-- Migration 004: Update dedup index to exclude merchant
--
-- Duplicate detection now groups by (date, amount, account_id) only,
-- so the old index that included merchant is replaced.

DROP INDEX IF EXISTS idx_tx_dedup_key;
CREATE INDEX idx_tx_dedup_key ON transactions(date, amount, account_id);
