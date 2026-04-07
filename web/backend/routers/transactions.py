"""
Transactions API endpoints.
"""

import sqlite3
from fastapi import APIRouter, HTTPException

from db import get_connection
from models import Transaction, TransactionUpdate, MoveTransactionRequest

router = APIRouter()


def _row_to_transaction(row) -> Transaction:
    """Convert a database row to a Transaction model."""
    return Transaction(
        id=row["id"],
        account_id=row["account_id"],
        statement_id=row["statement_id"],
        date=row["date"],
        merchant=row["merchant"],
        description=row["description"],
        currency=row["currency"],
        debit=row["debit"],
        credit=row["credit"],
        amount=row["amount"],
        tx_type=row["tx_type"],
        subtotal=row["subtotal"],
        taxes=row["taxes"],
        source_file=row["source_file"],
        imported_at=row["imported_at"],
        notification_status=row["notification_status"],
        duplicate_of=row["duplicate_of"],
        account_label=None,
    )


@router.get("/{tx_id}")
def get_transaction(tx_id: int) -> Transaction:
    """Get a single transaction by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (tx_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return _row_to_transaction(row)


@router.patch("/{tx_id}")
def update_transaction(tx_id: int, body: TransactionUpdate) -> Transaction:
    """Update editable fields of a transaction."""
    with get_connection() as conn:
        # Verify transaction exists
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (tx_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Build UPDATE statement only for non-null fields
        updates = {}
        if body.merchant is not None:
            updates["merchant"] = body.merchant
        if body.description is not None:
            updates["description"] = body.description
        if body.date is not None:
            updates["date"] = body.date
        if body.amount is not None:
            updates["amount"] = body.amount
            # Also update debit/credit based on tx_type
            if body.tx_type is not None:
                tx_type = body.tx_type
            else:
                tx_type = row["tx_type"]
            if tx_type == "debit":
                updates["debit"] = body.amount
                updates["credit"] = None
            else:
                updates["credit"] = body.amount
                updates["debit"] = None
        if body.tx_type is not None:
            updates["tx_type"] = body.tx_type
            # If amount is not being updated but tx_type is, still derive debit/credit
            if body.amount is None:
                amount = row["amount"]
                if body.tx_type == "debit":
                    updates["debit"] = amount
                    updates["credit"] = None
                else:
                    updates["credit"] = amount
                    updates["debit"] = None

        if not updates:
            # No changes
            return _row_to_transaction(row)

        # Perform UPDATE
        set_clauses = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [tx_id]

        try:
            conn.execute(
                f"UPDATE transactions SET {set_clauses} WHERE id = ?", values
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise HTTPException(
                status_code=409,
                detail=f"Conflict: {str(e)}",
            )

        # Re-fetch and return
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (tx_id,)
        ).fetchone()
        return _row_to_transaction(row)


@router.post("/{tx_id}/move")
def move_transaction(tx_id: int, body: MoveTransactionRequest) -> Transaction:
    """Move a transaction to a different account."""
    with get_connection() as conn:
        # Verify transaction exists
        tx_row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (tx_id,)
        ).fetchone()
        if not tx_row:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Verify target account exists
        target_acct = conn.execute(
            "SELECT id FROM accounts WHERE id = ?", (body.target_account_id,)
        ).fetchone()
        if not target_acct:
            raise HTTPException(status_code=404, detail="Target account not found")

        # Check if already on target account
        if tx_row["account_id"] == body.target_account_id:
            raise HTTPException(
                status_code=400,
                detail="Transaction is already on this account",
            )

        # Perform move: update account_id and detach from statement
        try:
            conn.execute(
                "UPDATE transactions SET account_id = ?, statement_id = NULL WHERE id = ?",
                (body.target_account_id, tx_id),
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise HTTPException(
                status_code=409,
                detail=f"Conflict: {str(e)}",
            )

        # Re-fetch and return
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (tx_id,)
        ).fetchone()
        return _row_to_transaction(row)
