"""
Accounts API endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from db import get_connection, WORKSPACE_ROOT
from models import Account, AccountDetail, Statement, TransactionPage, Transaction

router = APIRouter()


def _row_to_account(row, conn) -> Account:
    """Convert a database row to an Account model, enriching with latest balance."""
    # Query for latest DOP statement
    latest_stmt = conn.execute(
        """
        SELECT id, account_balance, currency, period_end
        FROM account_statements
        WHERE account_id = ? AND currency = 'DOP'
        ORDER BY period_end DESC
        LIMIT 1
        """,
        (row["id"],),
    ).fetchone()

    return Account(
        id=row["id"],
        institution=row["institution"],
        account_type=row["account_type"],
        account_product=row["account_product"],
        account_number_last4=row["account_number_last4"],
        credit_limit=row["credit_limit"],
        minimum_payment=row["minimum_payment"],
        original_balance=row["original_balance"],
        interest_rate_annual=row["interest_rate_annual"],
        apy=row["apy"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        latest_balance=latest_stmt["account_balance"] if latest_stmt else None,
        latest_balance_currency=latest_stmt["currency"] if latest_stmt else None,
        latest_statement_date=latest_stmt["period_end"] if latest_stmt else None,
    )


@router.get("")
def list_accounts() -> list[Account]:
    """Get all accounts with latest balances."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM accounts ORDER BY institution, account_type"
        ).fetchall()
        return [_row_to_account(row, conn) for row in rows]


@router.get("/{account_id}")
def get_account(account_id: int) -> AccountDetail:
    """Get a single account with all its statements."""
    with get_connection() as conn:
        acc_row = conn.execute(
            "SELECT * FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()
        if not acc_row:
            raise HTTPException(status_code=404, detail="Account not found")

        account = _row_to_account(acc_row, conn)

        stmt_rows = conn.execute(
            "SELECT * FROM account_statements WHERE account_id = ? ORDER BY period_end DESC",
            (account_id,),
        ).fetchall()
        statements = [
            Statement(
                id=s["id"],
                account_id=s["account_id"],
                period_start=s["period_start"],
                period_end=s["period_end"],
                currency=s["currency"],
                account_balance=s["account_balance"],
                cut_date=s["cut_date"],
                balance_at_cut=s["balance_at_cut"],
                payment_due_date=s["payment_due_date"],
                source_file=s["source_file"],
                imported_at=s["imported_at"],
            )
            for s in stmt_rows
        ]

        return AccountDetail(account=account, statements=statements)


@router.get("/{account_id}/transactions")
def get_account_transactions(
    account_id: int,
    limit: int = 100,
    offset: int = 0,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    currency: Optional[str] = None,
) -> TransactionPage:
    """Get transactions for an account with optional filtering."""
    with get_connection() as conn:
        # Verify account exists
        acc = conn.execute(
            "SELECT id FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")

        # Build query
        where_clauses = ["account_id = ?"]
        params = [account_id]

        if date_from:
            where_clauses.append("date >= ?")
            params.append(date_from)
        if date_to:
            where_clauses.append("date <= ?")
            params.append(date_to)
        if currency:
            where_clauses.append("currency = ?")
            params.append(currency)

        where_sql = " AND ".join(where_clauses)

        # Count total
        total = conn.execute(
            f"SELECT COUNT(*) as cnt FROM transactions WHERE {where_sql}",
            params,
        ).fetchone()["cnt"]

        # Fetch paginated
        rows = conn.execute(
            f"""
            SELECT * FROM transactions
            WHERE {where_sql}
            ORDER BY date DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ).fetchall()

        transactions = [
            Transaction(
                id=r["id"],
                account_id=r["account_id"],
                statement_id=r["statement_id"],
                date=r["date"],
                merchant=r["merchant"],
                currency=r["currency"],
                debit=r["debit"],
                credit=r["credit"],
                amount=r["amount"],
                tx_type=r["tx_type"],
                subtotal=r["subtotal"],
                taxes=r["taxes"],
                source_file=r["source_file"],
                imported_at=r["imported_at"],
                notification_status=r["notification_status"],
                account_label=None,
            )
            for r in rows
        ]

        return TransactionPage(transactions=transactions, total=total)
