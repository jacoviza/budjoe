-- Migration 006: Backfill notification_status = 'rejected' for existing duplicates
--
-- Any transaction already marked as a duplicate (duplicate_of IS NOT NULL)
-- should be treated as rejected for consistency.
UPDATE transactions
SET notification_status = 'rejected'
WHERE duplicate_of IS NOT NULL;
