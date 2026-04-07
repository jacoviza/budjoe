#!/usr/bin/env python3
"""
Interactive CLI for reviewing and resolving duplicate transactions.

Usage:
    python db/detect_duplicates.py

For each group of potential duplicates the script shows a numbered table and
offers four choices:
  [A] Confirm all as duplicates  — lowest ID is the original
  [N] None are duplicates        — add all pairs to exceptions
  [S] Select specific ones       — pick which rows are duplicates
  [K] Skip                       — leave this group for later
"""

import itertools
import sys
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Allow running from the repo root or from db/
sys.path.insert(0, str(Path(__file__).parent))

from lib import get_connection


# ──────────────────────────────────────────────────────────────────────────────
# DB helpers
# ──────────────────────────────────────────────────────────────────────────────

def load_exception_pairs(conn) -> set[tuple[int, int]]:
    rows = conn.execute("SELECT tx_id_a, tx_id_b FROM duplicate_exceptions").fetchall()
    return {(r["tx_id_a"], r["tx_id_b"]) for r in rows}


def group_is_fully_excepted(ids: list[int], exceptions: set[tuple[int, int]]) -> bool:
    for a, b in itertools.combinations(sorted(ids), 2):
        if (a, b) not in exceptions:
            return False
    return True


def fetch_groups(conn) -> list[dict]:
    """Return all unresolved duplicate groups as a list of dicts."""
    rows = conn.execute(
        """
        SELECT date, amount, account_id, tx_type,
               GROUP_CONCAT(id) AS ids
        FROM (SELECT * FROM transactions WHERE duplicate_of IS NULL ORDER BY id)
        GROUP BY date, amount, account_id, tx_type
        HAVING COUNT(*) > 1
        ORDER BY date DESC
        """
    ).fetchall()

    exceptions = load_exception_pairs(conn)
    groups = []
    for row in rows:
        ids = [int(i) for i in row["ids"].split(",")]
        if not group_is_fully_excepted(ids, exceptions):
            # Fetch full rows for display
            placeholders = ",".join("?" * len(ids))
            tx_rows = conn.execute(
                f"SELECT t.*, a.institution, a.account_type, a.account_number_last4 "
                f"FROM transactions t "
                f"LEFT JOIN accounts a ON a.id = t.account_id "
                f"WHERE t.id IN ({placeholders})",
                ids,
            ).fetchall()
            groups.append({
                "date": row["date"],
                "merchant": row["merchant"],
                "amount": row["amount"],
                "account_id": row["account_id"],
                "ids": ids,
                "txs": sorted(tx_rows, key=lambda r: r["id"]),
            })
    return groups


# ──────────────────────────────────────────────────────────────────────────────
# Display helpers
# ──────────────────────────────────────────────────────────────────────────────

def source_label(tx) -> str:
    if tx["statement_id"] is not None:
        return "statement"
    status = tx["notification_status"]
    if status is not None:
        return f"notification ({status})"
    return "receipt"


def account_label(tx) -> str:
    label = f"{tx['institution']} {tx['account_type']}"
    if tx["account_number_last4"]:
        label += f" ···{tx['account_number_last4']}"
    return label


def print_group(group: dict, index: int, total: int) -> None:
    txs = group["txs"]
    print()
    print(f"  Group {index} of {total}  —  {len(txs)} potential duplicates")
    print(f"  {group['date']}  ·  {group['merchant']}  ·  {group['amount']:,.2f}  ·  {account_label(txs[0])}")
    print("  " + "─" * 68)
    print(f"  {'#':<4} {'ID':<6} {'Date':<12} {'Amount':>10}  {'Source':<28} {'Imported':<20}")
    print("  " + "─" * 68)
    for i, tx in enumerate(txs, 1):
        src = source_label(tx)
        print(f"  {i:<4} {tx['id']:<6} {tx['date']:<12} {tx['amount']:>10,.2f}  {src:<28} {tx['imported_at'][:19]}")
    print("  " + "─" * 68)


# ──────────────────────────────────────────────────────────────────────────────
# Resolution actions
# ──────────────────────────────────────────────────────────────────────────────

def confirm_all(conn, ids: list[int]) -> str:
    original_id = ids[0]
    for dup_id in ids[1:]:
        conn.execute(
            "UPDATE transactions SET duplicate_of = ? WHERE id = ?",
            (original_id, dup_id),
        )
    conn.commit()
    return f"Marked {len(ids) - 1} transaction(s) as duplicates of ID {original_id}."


def dismiss_all(conn, ids: list[int]) -> str:
    for a, b in itertools.combinations(sorted(ids), 2):
        conn.execute(
            "INSERT OR IGNORE INTO duplicate_exceptions (tx_id_a, tx_id_b) VALUES (?, ?)",
            (min(a, b), max(a, b)),
        )
    conn.commit()
    return f"Recorded {len(list(itertools.combinations(ids, 2)))} exception pair(s). This group will not re-appear."


def confirm_selected(conn, all_ids: list[int], selected_numbers: list[int], txs: list) -> str:
    """selected_numbers is 1-based row numbers from the display table."""
    # Convert to 0-based indices
    try:
        selected_ids = [txs[n - 1]["id"] for n in selected_numbers]
    except IndexError:
        return "Invalid selection — numbers out of range. Skipped."

    selected_set = set(selected_ids)
    unselected = [i for i in all_ids if i not in selected_set]

    if not selected_ids:
        return "No rows selected. Skipped."

    # Confirm selected: lowest selected ID is the original
    original_id = sorted(selected_ids)[0]
    for dup_id in sorted(selected_ids):
        if dup_id != original_id:
            conn.execute(
                "UPDATE transactions SET duplicate_of = ? WHERE id = ?",
                (original_id, dup_id),
            )

    # Dismiss unselected pairs
    for a, b in itertools.combinations(sorted(unselected), 2):
        conn.execute(
            "INSERT OR IGNORE INTO duplicate_exceptions (tx_id_a, tx_id_b) VALUES (?, ?)",
            (min(a, b), max(a, b)),
        )

    conn.commit()
    confirmed = len(selected_ids) - 1
    dismissed = len(list(itertools.combinations(unselected, 2)))
    return (
        f"Marked {confirmed} transaction(s) as duplicates of ID {original_id}."
        + (f" Recorded {dismissed} exception pair(s) for unselected rows." if dismissed else "")
    )


# ──────────────────────────────────────────────────────────────────────────────
# Main loop
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    with get_connection() as conn:
        groups = fetch_groups(conn)

    if not groups:
        print("No duplicate groups found.")
        return

    total = len(groups)
    print(f"\nFound {total} potential duplicate group(s).\n")

    resolved = 0
    skipped = 0

    for idx, group in enumerate(groups, 1):
        print_group(group, idx, total)
        ids = group["ids"]
        txs = group["txs"]

        while True:
            print()
            print(f"  [A] Confirm all as duplicates  (ID {ids[0]} is original)")
            print("  [N] None are duplicates")
            print("  [S] Select specific duplicates")
            print("  [K] Skip this group")
            choice = input("  Choice: ").strip().upper()

            if choice == "A":
                with get_connection() as conn:
                    msg = confirm_all(conn, ids)
                print(f"  ✓ {msg}")
                resolved += 1
                break

            elif choice == "N":
                with get_connection() as conn:
                    msg = dismiss_all(conn, ids)
                print(f"  ✓ {msg}")
                resolved += 1
                break

            elif choice == "S":
                raw = input(
                    f"  Enter row numbers of DUPLICATE rows (comma-separated, 1–{len(txs)}): "
                ).strip()
                try:
                    selected_numbers = [int(x.strip()) for x in raw.split(",") if x.strip()]
                except ValueError:
                    print("  Invalid input. Please enter numbers only.")
                    continue
                if not selected_numbers:
                    print("  No rows selected. Please try again.")
                    continue
                with get_connection() as conn:
                    msg = confirm_selected(conn, ids, selected_numbers, txs)
                print(f"  ✓ {msg}")
                resolved += 1
                break

            elif choice == "K":
                print("  Skipped.")
                skipped += 1
                break

            else:
                print("  Unknown choice. Please enter A, N, S, or K.")

        remaining = total - idx
        if remaining > 0:
            print(f"\n  ── Resolved {resolved}, skipped {skipped}, {remaining} group(s) remaining ──")

    print(f"\nDone. Resolved {resolved} group(s), skipped {skipped} group(s).")


if __name__ == "__main__":
    main()
