#!/usr/bin/env python3
"""
db/load_notification.py — Import bank notification files into finance.db.

Scans bank-notifications/01-transactions-to-load/ for files with status: pending,
loads each one into the transactions table with notification_status = 'pending',
then updates the file status to 'imported' and moves it to 02-loaded-transactions/.

Idempotent: re-running on an already-imported file prints "Already imported. Skipping."

Usage:
    python db/load_notification.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import (
    get_connection,
    get_or_create_account,
    parse_kv_table,
    parse_yaml_kv,
    parse_number,
    receipt_already_imported,
    relative_path,
)

WORKSPACE_ROOT = Path(__file__).parent.parent
TRANSACTIONS_DIR = WORKSPACE_ROOT / "bank-notifications" / "01-transactions-to-load"
LOADED_DIR = WORKSPACE_ROOT / "bank-notifications" / "02-loaded-transactions"
ACCOUNT_TYPE_MEMORY = Path(__file__).parent / "account_type_memory.json"

VALID_ACCOUNT_TYPES = ("checking", "savings", "credit_card", "loan", "mortgage", "cash")


# ── Account-type memory ───────────────────────────────────────────────────────

def _load_memory() -> dict:
    if ACCOUNT_TYPE_MEMORY.exists():
        return json.loads(ACCOUNT_TYPE_MEMORY.read_text(encoding="utf-8"))
    return {}


def _save_memory(memory: dict) -> None:
    ACCOUNT_TYPE_MEMORY.write_text(
        json.dumps(memory, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def resolve_debit_card_type(institution: str, last4: str | None, memory: dict) -> str:
    """
    Return the real account_type for a debit card.
    Checks memory; raises SystemExit with a structured message if not found.
    """
    key = f"{institution}:{last4 or 'unknown'}"

    if key in memory:
        resolved = memory[key]
        print(f"  [memory] {key} -> {resolved}")
        return resolved

    label = f"{institution} debit card" + (f" ending in {last4}" if last4 else "")
    print(
        f"\nNEEDS_RESOLUTION: {key}\n"
        f"  Unknown account type for {label}.\n"
        f"  Add an entry to db/account_type_memory.json:\n"
        f'    "{key}": "checking"  or  "savings"\n'
        f"  Then re-run the loader.",
        file=sys.stderr,
    )
    sys.exit(2)


# ── Parsing ───────────────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML frontmatter between the first pair of --- markers."""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return parse_yaml_kv(parts[1])


def set_status(path: Path, new_status: str) -> None:
    """Replace status: <value> in the frontmatter block and write back."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    in_frontmatter = False
    fm_count = 0
    result = []
    for line in lines:
        if line.strip() == "---":
            fm_count += 1
            in_frontmatter = fm_count == 1
            result.append(line)
            if fm_count == 2:
                in_frontmatter = False
            continue
        if in_frontmatter and line.strip().startswith("status:"):
            result.append(f"status: {new_status}\n")
        else:
            result.append(line)
    path.write_text("".join(result), encoding="utf-8")


def get_pending_files() -> list[Path]:
    """Return all .md files in transactions/ with status: pending."""
    pending = []
    for path in sorted(TRANSACTIONS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm.get("status", "").strip() == "pending":
            pending.append(path)
    return pending


# ── Loader ────────────────────────────────────────────────────────────────────

def load_notification(path: Path, memory: dict) -> bool:
    """
    Load one notification file into the transactions table.
    Returns True on success, False on error.
    """
    src = relative_path(path)

    with get_connection() as conn:
        if receipt_already_imported(conn, src):
            print(f"  Already imported: {path.name}. Skipping.")
            return True

        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        tx = parse_kv_table(text)

        # Required fields from frontmatter
        institution  = fm.get("institution", "").strip()
        account_type = fm.get("account_type", "").strip()
        last4        = fm.get("account_number_last4", "").strip() or None

        if account_type == "debit_card":
            account_type = resolve_debit_card_type(institution, last4, memory)

        # Required fields from table
        amount_raw   = tx.get("amount", "")
        currency     = tx.get("currency", "DOP").strip()
        merchant     = tx.get("merchant", "").strip()
        datetime_str = tx.get("datetime", "").strip()
        tx_type      = tx.get("tx_type", "debit").strip().lower()

        # Validation
        if not institution:
            print(f"  ERROR: missing institution in {path.name}", file=sys.stderr)
            return False
        if not account_type:
            print(f"  ERROR: missing account_type in {path.name}", file=sys.stderr)
            return False
        if not merchant:
            print(f"  ERROR: missing merchant in {path.name}", file=sys.stderr)
            return False

        amount = parse_number(amount_raw)
        if amount is None:
            print(f"  ERROR: could not parse amount '{amount_raw}' in {path.name}", file=sys.stderr)
            return False

        date = datetime_str[:10] if datetime_str else fm.get("email_date", "")[:10]
        if not date:
            print(f"  ERROR: could not determine date in {path.name}", file=sys.stderr)
            return False

        if tx_type not in ("debit", "credit"):
            print(f"  ERROR: invalid tx_type '{tx_type}' in {path.name}", file=sys.stderr)
            return False

        debit  = amount if tx_type == "debit"  else None
        credit = amount if tx_type == "credit" else None

        account_id = get_or_create_account(
            conn,
            institution=institution,
            account_type=account_type,
            account_number_last4=last4,
        )

        conn.execute(
            """
            INSERT INTO transactions (
                account_id, statement_id,
                date, merchant, currency,
                debit, credit, amount, tx_type,
                subtotal, taxes,
                source_file, notification_status
            ) VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, 'pending')
            """,
            (account_id, date, merchant, currency, debit, credit, amount, tx_type, src),
        )
        conn.commit()

    set_status(path, "imported")
    LOADED_DIR.mkdir(exist_ok=True)
    path.rename(LOADED_DIR / path.name)
    print(f"  Imported: {merchant} ({date}) — {amount:,.2f} {currency} [pending review]")
    return True


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    if not TRANSACTIONS_DIR.exists():
        print(
            f"ERROR: {TRANSACTIONS_DIR} does not exist.\n"
            "Run the scan workflow first to populate bank-notifications/01-transactions-to-load/",
            file=sys.stderr,
        )
        sys.exit(1)

    pending = get_pending_files()

    if not pending:
        print("No pending files found in bank-notifications/01-transactions-to-load/")
        sys.exit(0)

    print(f"Loading {len(pending)} pending file(s)...\n")
    memory = _load_memory()
    ok = err = 0
    for path in pending:
        if load_notification(path, memory):
            ok += 1
        else:
            err += 1

    print(f"\nDone.  Imported: {ok}  Errors: {err}")
    if ok:
        print("Transactions are marked notification_status='pending' and await review.")


if __name__ == "__main__":
    main()
