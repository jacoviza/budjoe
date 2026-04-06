"""
db/lib.py — Shared utilities for the finance DB loaders.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────

DB_PATH = Path(__file__).parent / "finance.db"
WORKSPACE_ROOT = Path(__file__).parent.parent


def relative_path(abs_path: str | Path) -> str:
    """Return workspace-root-relative POSIX path for use as source_file key."""
    try:
        return Path(abs_path).resolve().relative_to(WORKSPACE_ROOT.resolve()).as_posix()
    except ValueError:
        return str(abs_path)


# ── Connection ────────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ── Timestamps ────────────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Number parsing ────────────────────────────────────────────────────────────

def parse_number(s: str | None) -> float | None:
    """Strip commas and percent signs, return float or None."""
    if not s or not s.strip():
        return None
    try:
        return float(s.strip().replace(",", "").replace("%", ""))
    except ValueError:
        return None


# ── Institution normalisation ─────────────────────────────────────────────────

INSTITUTION_ALIASES: dict[str, str] = {
    "bhd":                              "BHD",
    "bhd león":                         "BHD",
    "scotiabank":                       "Scotiabank",
    "scotiabank república dominicana":  "Scotiabank",
    "qik":                              "Qik",
    "qik banco digital dominicano":     "Qik",
    "cash":                             "cash",
}


def normalize_institution(name: str) -> str:
    return INSTITUTION_ALIASES.get(name.strip().lower(), name.strip())


# ── Account management ────────────────────────────────────────────────────────

def get_or_create_account(
    conn: sqlite3.Connection,
    institution: str,
    account_type: str,
    account_product: str | None = None,
    account_number_last4: str | None = None,
    credit_limit: float | None = None,
    minimum_payment: float | None = None,
    original_balance: float | None = None,
    interest_rate_annual: str | None = None,
    apy: str | None = None,
) -> int:
    """Upsert account; return its id."""
    institution = normalize_institution(institution)

    row = conn.execute(
        """
        SELECT id FROM accounts
        WHERE institution = ?
          AND account_type = ?
          AND (account_product IS ? OR account_product = ?)
        """,
        (institution, account_type, account_product, account_product),
    ).fetchone()

    if row:
        account_id = row["id"]
        # Update last4 if we now have it
        if account_number_last4:
            conn.execute(
                "UPDATE accounts SET account_number_last4 = ?, updated_at = ? WHERE id = ?",
                (account_number_last4, now_iso(), account_id),
            )
        return account_id

    # First import — create record
    conn.execute(
        """
        INSERT INTO accounts (
            institution, account_type, account_product, account_number_last4,
            credit_limit, minimum_payment, original_balance,
            interest_rate_annual, apy
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            institution, account_type, account_product, account_number_last4,
            credit_limit, minimum_payment, original_balance,
            interest_rate_annual, apy,
        ),
    )
    account_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    print(f"  Created account: {institution} — {account_type}"
          + (f" ({account_product})" if account_product else ""))
    return account_id


def get_or_create_cash_account(conn: sqlite3.Connection) -> int:
    """Return the id of the virtual cash account, creating it if needed."""
    return get_or_create_account(
        conn,
        institution="cash",
        account_type="cash",
        account_product="Virtual Cash Account",
    )


# ── Deduplication checks ──────────────────────────────────────────────────────

def statement_already_imported(conn: sqlite3.Connection, source_file: str) -> bool:
    """True if any row for this source_file exists in account_statements."""
    row = conn.execute(
        "SELECT 1 FROM account_statements WHERE source_file = ? LIMIT 1",
        (source_file,),
    ).fetchone()
    return row is not None


def receipt_already_imported(conn: sqlite3.Connection, source_file: str) -> bool:
    """True if any transaction row for this source_file exists."""
    row = conn.execute(
        "SELECT 1 FROM transactions WHERE source_file = ? LIMIT 1",
        (source_file,),
    ).fetchone()
    return row is not None


# ── Markdown table parsers ────────────────────────────────────────────────────

def parse_kv_table(block: str) -> dict[str, str]:
    """
    Parse a vertical | Field | Value | markdown table into a dict.
    Skips header and separator rows.
    """
    result: dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) == 2 and parts[0].lower() not in ("field",):
            result[parts[0]] = parts[1]
    return result


def parse_yaml_kv(block: str) -> dict[str, str]:
    """Parse bare 'key: value' lines (simple YAML subset, no nesting)."""
    result: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line and not line.strip().startswith("#"):
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


def normalize_header(h: str) -> str:
    """Normalize column header names for the transaction table."""
    h = h.lower().strip()
    if h in ("merchant / description", "merchant/description", "description"):
        return "merchant"
    return h


def parse_tx_table(block: str) -> list[dict]:
    """
    Parse a horizontal markdown transaction table.
    Returns list of dicts with keys: date, merchant, debit, credit.
    Skips rows where both debit and credit are empty/zero.
    """
    rows: list[dict] = []
    headers: list[str] | None = None

    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if "---" in line:
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if not cells:
            continue

        if headers is None:
            headers = [normalize_header(h) for h in cells]
            continue

        # Pad short rows
        while len(cells) < len(headers):
            cells.append("")
        row = dict(zip(headers, cells))

        debit = parse_number(row.get("debit", ""))
        credit = parse_number(row.get("credit", ""))
        if debit is None and credit is None:
            continue

        rows.append({
            "date":    row.get("date", "").strip(),
            "merchant": row.get("merchant", "").strip(),
            "debit":   debit,
            "credit":  credit,
        })

    return rows
