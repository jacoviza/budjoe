-- Migration 005: Add description column to transactions
ALTER TABLE transactions ADD COLUMN description TEXT;
