-- Add notification_status to transactions.
-- Notification-sourced transactions are imported with notification_status = 'pending'.
-- Receipts and statement imports leave it NULL (not applicable).
-- The future approval workflow will flip this to 'approved' or 'rejected'.
ALTER TABLE transactions ADD COLUMN notification_status TEXT
    CHECK (notification_status IN ('pending', 'approved', 'rejected'));
