-- Migration 003: Duplicate transaction detection
--
-- Adds duplicate_of column so confirmed duplicates point to their original.
-- Chain rule: duplicate_of must point only to rows where duplicate_of IS NULL
--             (enforced at application level, not DB level).
-- Also adds duplicate_exceptions table to remember pairs the user confirmed
-- are NOT duplicates, preventing them from re-surfacing.

ALTER TABLE transactions ADD COLUMN duplicate_of INTEGER REFERENCES transactions(id);

-- Fast lookup: "which transactions are duplicates of X?"
CREATE INDEX idx_tx_duplicate_of ON transactions(duplicate_of);

-- Fast duplicate-group detection by the natural key
CREATE INDEX idx_tx_dedup_key ON transactions(date, merchant, amount, account_id);

-- Pairs explicitly confirmed as NOT duplicates.
-- tx_id_a < tx_id_b enforced by CHECK so each pair is stored once.
CREATE TABLE duplicate_exceptions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_id_a    INTEGER NOT NULL REFERENCES transactions(id),
    tx_id_b    INTEGER NOT NULL REFERENCES transactions(id),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    CHECK (tx_id_a < tx_id_b),
    UNIQUE (tx_id_a, tx_id_b)
);
