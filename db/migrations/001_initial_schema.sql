-- Migration 001: Initial schema
-- accounts, account_statements, transactions tables + indexes

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- accounts
-- One row per institution + account_type + account_product.
-- Type-specific columns are nullable; only populated when relevant.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS accounts (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    institution          TEXT    NOT NULL,
    account_type         TEXT    NOT NULL CHECK (account_type IN (
                             'checking', 'savings', 'credit_card',
                             'loan', 'mortgage', 'cash'
                         )),
    account_product      TEXT,            -- e.g. "Scotiamax", "AMEX SUMA CCN"
    account_number_last4 TEXT,            -- e.g. "7925", "1114"

    -- credit_card only
    credit_limit         REAL,
    minimum_payment      REAL,

    -- loan / mortgage only
    original_balance     REAL,
    interest_rate_annual TEXT,            -- stored as string to preserve "0.15%"

    -- savings only
    apy                  TEXT,

    created_at           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    UNIQUE (institution, account_type, account_product)
);

-- ------------------------------------------------------------
-- account_statements
-- One row per (source_file, currency). A multi-currency statement
-- file produces multiple rows, all pointing to the same account_id.
-- Deduplication: UNIQUE (source_file, currency).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS account_statements (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id       INTEGER NOT NULL REFERENCES accounts(id),
    period_start     TEXT    NOT NULL,   -- YYYY-MM-DD
    period_end       TEXT    NOT NULL,   -- YYYY-MM-DD
    currency         TEXT    NOT NULL,   -- ISO 4217: DOP, USD, etc.
    account_balance  REAL,               -- closing balance for this currency

    -- credit_card / loan / mortgage specific
    cut_date         TEXT,               -- YYYY-MM-DD
    balance_at_cut   REAL,
    payment_due_date TEXT,               -- YYYY-MM-DD

    source_file      TEXT    NOT NULL,   -- workspace-root-relative path
    imported_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    UNIQUE (source_file, currency)
);

CREATE INDEX IF NOT EXISTS idx_stmt_account ON account_statements(account_id);
CREATE INDEX IF NOT EXISTS idx_stmt_period  ON account_statements(period_end);

-- ------------------------------------------------------------
-- transactions
-- Unified table for statement transactions and receipts.
-- statement_id is NULL for receipts.
-- account_id is always set (receipts use the cash virtual account
-- or a user-selected real account).
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id   INTEGER REFERENCES accounts(id),
    statement_id INTEGER REFERENCES account_statements(id),

    date         TEXT    NOT NULL,       -- YYYY-MM-DD
    merchant     TEXT    NOT NULL,
    currency     TEXT    NOT NULL DEFAULT 'DOP',
    debit        REAL,                   -- raw debit column value (NULL if credit-only)
    credit       REAL,                   -- raw credit column value (NULL if debit-only)
    amount       REAL    NOT NULL,       -- always positive; direction in tx_type
    tx_type      TEXT    NOT NULL CHECK (tx_type IN ('debit', 'credit')),

    -- receipt-only fields
    subtotal     REAL,
    taxes        REAL,

    source_file  TEXT    NOT NULL,       -- workspace-root-relative path
    imported_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_tx_account   ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_tx_date      ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_tx_statement ON transactions(statement_id);

-- Dedup within a statement: same statement + date + merchant + amount + direction
CREATE UNIQUE INDEX IF NOT EXISTS idx_tx_dedup
    ON transactions(statement_id, date, merchant, amount, tx_type)
    WHERE statement_id IS NOT NULL;
