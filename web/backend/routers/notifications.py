"""
Notifications API endpoints.
"""

from fastapi import APIRouter, HTTPException

from db import get_connection
from models import Transaction, NotificationStatusUpdate, BulkNotificationUpdate

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


@router.get("/pending")
def get_pending_notifications() -> list[Transaction]:
    """Get all transactions with notification_status = 'pending'."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM transactions
            WHERE notification_status = 'pending'
            ORDER BY date DESC
            """
        ).fetchall()
        return [_row_to_transaction(row) for row in rows]


@router.patch("/{tx_id}/status")
def update_notification_status(
    tx_id: int, body: NotificationStatusUpdate
) -> dict:
    """Update the notification_status of a single transaction."""
    with get_connection() as conn:
        # Verify transaction exists
        row = conn.execute(
            "SELECT * FROM transactions WHERE id = ?", (tx_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Validate status
        if body.status not in ("approved", "rejected"):
            raise HTTPException(
                status_code=400,
                detail="Status must be 'approved' or 'rejected'",
            )

        # Update
        conn.execute(
            "UPDATE transactions SET notification_status = ? WHERE id = ?",
            (body.status, tx_id),
        )
        conn.commit()

        return {"id": tx_id, "notification_status": body.status}


@router.post("/bulk-status")
def bulk_update_notification_status(body: BulkNotificationUpdate) -> dict:
    """Bulk update notification_status for multiple transactions."""
    with get_connection() as conn:
        # Validate status
        if body.status not in ("approved", "rejected"):
            raise HTTPException(
                status_code=400,
                detail="Status must be 'approved' or 'rejected'",
            )

        # Build placeholders for IN clause
        placeholders = ",".join("?" * len(body.transaction_ids))

        # Update
        conn.execute(
            f"UPDATE transactions SET notification_status = ? WHERE id IN ({placeholders})",
            [body.status] + body.transaction_ids,
        )
        conn.commit()

        return {"updated": len(body.transaction_ids)}
