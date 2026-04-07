"""
Duplicate transaction detection and resolution endpoints.
"""

import itertools
import sqlite3

from fastapi import APIRouter, HTTPException

from db import get_connection
from models import (
    DuplicateGroup,
    DuplicateGroupPage,
    DuplicateStats,
    DuplicateTransaction,
    ResolveAction,
    ResolveDuplicatesRequest,
)

router = APIRouter()


def _account_label(conn, account_id: int) -> str | None:
    row = conn.execute(
        "SELECT institution, account_type, account_product, account_number_last4 FROM accounts WHERE id = ?",
        (account_id,),
    ).fetchone()
    if not row:
        return None
    label = f"{row['institution']} {row['account_type']}"
    if row["account_product"]:
        label += f" {row['account_product']}"
    if row["account_number_last4"]:
        label += f" ···{row['account_number_last4']}"
    return label


def _load_exception_pairs(conn) -> set[tuple[int, int]]:
    """Return all exception pairs as a set of (min_id, max_id) tuples."""
    rows = conn.execute("SELECT tx_id_a, tx_id_b FROM duplicate_exceptions").fetchall()
    return {(r["tx_id_a"], r["tx_id_b"]) for r in rows}


def _group_is_fully_excepted(ids: list[int], exceptions: set[tuple[int, int]]) -> bool:
    """True if every pair in this group has been recorded as a non-duplicate exception."""
    for a, b in itertools.combinations(sorted(ids), 2):
        if (a, b) not in exceptions:
            return False
    return True


def _fetch_groups(conn, limit: int, offset: int) -> tuple[list[DuplicateGroup], int]:
    """Return (page_of_groups, total_unresolved_groups)."""
    # Find all candidate groups: same key, no member already confirmed as duplicate
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

    exceptions = _load_exception_pairs(conn)

    # Filter out fully-excepted groups
    active_groups = []
    for row in rows:
        ids = [int(i) for i in row["ids"].split(",")]
        if not _group_is_fully_excepted(ids, exceptions):
            active_groups.append((row, ids))

    total = len(active_groups)
    page = active_groups[offset : offset + limit]

    groups = []
    for row, ids in page:
        key = f"{row['date']}|{row['amount']}|{row['account_id']}|{row['tx_type']}"
        tx_rows = conn.execute(
            f"SELECT * FROM transactions WHERE id IN ({','.join('?' * len(ids))})",
            ids,
        ).fetchall()
        label = _account_label(conn, row["account_id"])
        txs = [
            DuplicateTransaction(
                id=r["id"],
                date=r["date"],
                merchant=r["merchant"],
                description=r["description"],
                amount=r["amount"],
                tx_type=r["tx_type"],
                currency=r["currency"],
                account_id=r["account_id"],
                account_label=label,
                source_file=r["source_file"],
                statement_id=r["statement_id"],
                notification_status=r["notification_status"],
                imported_at=r["imported_at"],
                duplicate_of=r["duplicate_of"],
            )
            for r in sorted(tx_rows, key=lambda x: x["id"])
        ]
        groups.append(DuplicateGroup(key=key, transactions=txs))

    return groups, total


@router.get("/groups")
def get_duplicate_groups(limit: int = 10, offset: int = 0) -> DuplicateGroupPage:
    """Return paginated unresolved duplicate groups."""
    with get_connection() as conn:
        groups, total = _fetch_groups(conn, limit, offset)
        return DuplicateGroupPage(groups=groups, total=total)


@router.get("/stats")
def get_duplicate_stats() -> DuplicateStats:
    """Return count of unresolved duplicate groups and transactions."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT GROUP_CONCAT(id) AS ids, date, amount, account_id, tx_type
            FROM (SELECT * FROM transactions WHERE duplicate_of IS NULL ORDER BY id)
            GROUP BY date, amount, account_id, tx_type
            HAVING COUNT(*) > 1
            """
        ).fetchall()

        exceptions = _load_exception_pairs(conn)
        total_groups = 0
        total_dupes = 0

        for row in rows:
            ids = [int(i) for i in row["ids"].split(",")]
            if not _group_is_fully_excepted(ids, exceptions):
                total_groups += 1
                total_dupes += len(ids) - 1  # originals don't count

        return DuplicateStats(
            total_groups=total_groups,
            total_duplicate_transactions=total_dupes,
        )


@router.post("/resolve")
def resolve_duplicates(body: ResolveDuplicatesRequest) -> dict:
    """
    Resolve one duplicate group.

    CONFIRM_ALL    — lowest ID is original, rest get duplicate_of = lowest_id
    DISMISS_ALL    — add all pairs to duplicate_exceptions
    CONFIRM_SELECTED — selected_duplicate_ids get duplicate_of = min(selected),
                       all pairs that mix unselected+unselected go to exceptions
    """
    if not body.transaction_ids:
        raise HTTPException(status_code=400, detail="transaction_ids must not be empty")

    with get_connection() as conn:
        # Validate all IDs exist and none are already confirmed duplicates
        placeholders = ",".join("?" * len(body.transaction_ids))
        rows = conn.execute(
            f"SELECT id, duplicate_of FROM transactions WHERE id IN ({placeholders})",
            body.transaction_ids,
        ).fetchall()

        found_ids = {r["id"] for r in rows}
        missing = set(body.transaction_ids) - found_ids
        if missing:
            raise HTTPException(status_code=404, detail=f"Transactions not found: {missing}")

        already_dupes = [r["id"] for r in rows if r["duplicate_of"] is not None]
        if already_dupes:
            raise HTTPException(
                status_code=400,
                detail=f"Transactions already marked as duplicates: {already_dupes}",
            )

        try:
            if body.action == ResolveAction.CONFIRM_ALL:
                _confirm_all(conn, sorted(body.transaction_ids))

            elif body.action == ResolveAction.DISMISS_ALL:
                _dismiss_all(conn, sorted(body.transaction_ids))

            elif body.action == ResolveAction.CONFIRM_SELECTED:
                if not body.selected_duplicate_ids:
                    raise HTTPException(
                        status_code=400,
                        detail="selected_duplicate_ids required for CONFIRM_SELECTED",
                    )
                _confirm_selected(
                    conn,
                    sorted(body.transaction_ids),
                    sorted(body.selected_duplicate_ids),
                )

            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise HTTPException(status_code=409, detail=f"Conflict: {e}")

        return {"status": "ok", "action": body.action}


def _confirm_all(conn, ids: list[int]) -> None:
    """Mark all but the lowest ID as duplicates of the lowest ID."""
    original_id = ids[0]
    # Verify original has no duplicate_of (chain rule)
    row = conn.execute("SELECT duplicate_of FROM transactions WHERE id = ?", (original_id,)).fetchone()
    if row["duplicate_of"] is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Transaction {original_id} is itself a duplicate — cannot be an original",
        )
    for dup_id in ids[1:]:
        conn.execute(
            "UPDATE transactions SET duplicate_of = ?, notification_status = 'rejected' WHERE id = ?",
            (original_id, dup_id),
        )


def _dismiss_all(conn, ids: list[int]) -> None:
    """Add all pairwise combinations to duplicate_exceptions."""
    for a, b in itertools.combinations(ids, 2):
        conn.execute(
            "INSERT OR IGNORE INTO duplicate_exceptions (tx_id_a, tx_id_b) VALUES (?, ?)",
            (min(a, b), max(a, b)),
        )


def _confirm_selected(conn, all_ids: list[int], selected_ids: list[int]) -> None:
    """
    Mark selected_ids as duplicates of min(selected_ids).
    Pairs of unselected IDs go to exceptions so they don't resurface together.
    """
    selected_set = set(selected_ids)
    unselected = [i for i in all_ids if i not in selected_set]

    # Validate selected IDs are a subset of all IDs
    unknown = selected_set - set(all_ids)
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"selected_duplicate_ids not in transaction_ids: {unknown}",
        )

    # Confirm selected
    original_id = selected_ids[0]
    row = conn.execute("SELECT duplicate_of FROM transactions WHERE id = ?", (original_id,)).fetchone()
    if row["duplicate_of"] is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Transaction {original_id} is itself a duplicate — cannot be an original",
        )
    for dup_id in selected_ids[1:]:
        conn.execute(
            "UPDATE transactions SET duplicate_of = ?, notification_status = 'rejected' WHERE id = ?",
            (original_id, dup_id),
        )

    # Dismiss unselected pairs so they never resurface as a group
    for a, b in itertools.combinations(unselected, 2):
        conn.execute(
            "INSERT OR IGNORE INTO duplicate_exceptions (tx_id_a, tx_id_b) VALUES (?, ?)",
            (min(a, b), max(a, b)),
        )
