#!/usr/bin/env python3
"""
db/load_receipt.py — Import a receipt transform file into finance.db.

Usage:
    python db/load_receipt.py <path-to-receipt-transform.md>

If real accounts exist in the DB, the user is prompted to choose which
account was used. Falls back to the virtual cash account when no real
accounts exist or the user selects "Cash / other".
"""

import sys
from pathlib import Path

# Allow running from the workspace root
sys.path.insert(0, str(Path(__file__).parent))

from lib import (
    get_connection,
    get_or_create_cash_account,
    parse_kv_table,
    parse_number,
    receipt_already_imported,
    relative_path,
)


# ── Account prompt ────────────────────────────────────────────────────────────

def prompt_account(conn, receipt_info: dict) -> int:
    """
    Ask the user which account a receipt belongs to.
    Returns account_id.
    """
    accounts = conn.execute(
        """
        SELECT id, institution, account_type, account_product, account_number_last4
        FROM accounts
        WHERE account_type != 'cash'
        ORDER BY institution, account_type, account_product
        """
    ).fetchall()

    if not accounts:
        return get_or_create_cash_account(conn)

    merchant = receipt_info.get("merchant", "?")
    date     = receipt_info.get("date", "?")
    total    = receipt_info.get("total", "?")

    print(f"\n  Receipt : {merchant}")
    print(f"  Date    : {date}    Total: {total}")
    print("\n  Which account was used for this purchase?\n")

    for i, acc in enumerate(accounts, 1):
        label = f"{acc['institution']} — {acc['account_type']}"
        if acc["account_product"]:
            label += f" ({acc['account_product']})"
        if acc["account_number_last4"]:
            label += f" ****{acc['account_number_last4']}"
        print(f"    {i}. {label}")

    cash_option = len(accounts) + 1
    print(f"    {cash_option}. Cash / other (no account)")

    while True:
        try:
            raw = input("\n  Enter number: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelled — assigning to cash.")
            return get_or_create_cash_account(conn)

        if raw.isdigit():
            n = int(raw)
            if 1 <= n <= len(accounts):
                return accounts[n - 1]["id"]
            if n == cash_option:
                return get_or_create_cash_account(conn)

        print("  Invalid selection — try again.")


# ── Parser ────────────────────────────────────────────────────────────────────

def parse_receipt(text: str) -> dict:
    """
    Parse a 5-field receipt markdown table.
    Returns dict with: datetime, merchant, subtotal, total, taxes.
    """
    data = parse_kv_table(text)
    return {
        "datetime": data.get("datetime", ""),
        "merchant": data.get("merchant", ""),
        "subtotal": parse_number(data.get("subtotal")),
        "total":    parse_number(data.get("total")),
        "taxes":    parse_number(data.get("taxes")),
    }


# ── Loader ────────────────────────────────────────────────────────────────────

def load_receipt(filepath: str) -> None:
    path = Path(filepath).resolve()
    src  = relative_path(path)

    with get_connection() as conn:
        if receipt_already_imported(conn, src):
            print(f"Already imported: {src}. Skipping.")
            return

        text    = path.read_text(encoding="utf-8")
        receipt = parse_receipt(text)

        if not receipt["total"]:
            print(f"ERROR: could not parse total from {path.name}", file=sys.stderr)
            sys.exit(1)

        date = receipt["datetime"][:10]  # YYYY-MM-DD
        receipt["date"] = date

        account_id = prompt_account(conn, receipt)

        amount  = receipt["total"]
        conn.execute(
            """
            INSERT INTO transactions (
                account_id, statement_id,
                date, merchant, currency,
                debit, credit, amount, tx_type,
                subtotal, taxes,
                source_file
            ) VALUES (?, NULL, ?, ?, 'DOP', ?, NULL, ?, 'debit', ?, ?, ?)
            """,
            (
                account_id,
                date,
                receipt["merchant"],
                amount,   # debit
                amount,   # amount
                receipt["subtotal"],
                receipt["taxes"],
                src,
            ),
        )
        conn.commit()

    print(f"  Imported receipt: {receipt['merchant']} ({date}) — {amount}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python db/load_receipt.py <receipt-transform.md>", file=sys.stderr)
        sys.exit(1)
    load_receipt(sys.argv[1])


if __name__ == "__main__":
    main()
