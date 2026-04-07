"""
Pydantic models for API request/response shapes.
"""

from enum import Enum

from pydantic import BaseModel
from typing import Optional


# ===== Response Models =====

class Account(BaseModel):
    """A financial account with optional enriched balance from latest statement."""
    id: int
    institution: str
    account_type: str
    account_product: Optional[str]
    account_number_last4: Optional[str]
    credit_limit: Optional[float]
    minimum_payment: Optional[float]
    original_balance: Optional[float]
    interest_rate_annual: Optional[str]
    apy: Optional[str]
    created_at: str
    updated_at: str
    # Enriched fields
    latest_balance: Optional[float]
    latest_balance_currency: Optional[str]
    latest_statement_date: Optional[str]


class Statement(BaseModel):
    """A bank account statement covering a period and currency."""
    id: int
    account_id: int
    period_start: str
    period_end: str
    currency: str
    account_balance: Optional[float]
    cut_date: Optional[str]
    balance_at_cut: Optional[float]
    payment_due_date: Optional[str]
    source_file: str
    imported_at: str


class Transaction(BaseModel):
    """A single transaction from any source (statement, receipt, or notification)."""
    id: int
    account_id: int
    statement_id: Optional[int]
    date: str
    merchant: str
    currency: str
    debit: Optional[float]
    credit: Optional[float]
    amount: float
    tx_type: str
    subtotal: Optional[float]
    taxes: Optional[float]
    source_file: str
    imported_at: str
    notification_status: Optional[str]
    duplicate_of: Optional[int]
    # Denormalized for display
    account_label: Optional[str]


class AccountDetail(BaseModel):
    """An account with its statements."""
    account: Account
    statements: list[Statement]


class TransactionPage(BaseModel):
    """Paginated transaction list."""
    transactions: list[Transaction]
    total: int


# ===== Request Models =====

class TransactionUpdate(BaseModel):
    """Update fields for a transaction."""
    merchant: Optional[str] = None
    date: Optional[str] = None
    amount: Optional[float] = None
    tx_type: Optional[str] = None  # 'debit' | 'credit'


class MoveTransactionRequest(BaseModel):
    """Move a transaction to a different account."""
    target_account_id: int


class NotificationStatusUpdate(BaseModel):
    """Update a single notification status."""
    status: str  # 'approved' | 'rejected'


class BulkNotificationUpdate(BaseModel):
    """Bulk update notification statuses."""
    transaction_ids: list[int]
    status: str


# ===== Action Response Models =====

class ActionResult(BaseModel):
    """Result of running a subprocess action."""
    success: bool
    stdout: str
    stderr: str
    return_code: int


class PendingFilesResult(BaseModel):
    """Lists of unprocessed files."""
    notification_files: list[str]  # filenames only
    receipt_transforms: list[str]
    statement_transforms: list[str]


# ===== Duplicate Detection Models =====

class DuplicateTransaction(BaseModel):
    """A transaction as shown inside a duplicate group."""
    id: int
    date: str
    merchant: str
    amount: float
    tx_type: str
    currency: str
    account_id: int
    account_label: Optional[str]
    source_file: str
    statement_id: Optional[int]
    notification_status: Optional[str]
    imported_at: str
    duplicate_of: Optional[int]


class DuplicateGroup(BaseModel):
    """A group of transactions sharing the same (date, merchant, amount, account_id)."""
    key: str  # "{date}|{merchant}|{amount}|{account_id}"
    transactions: list[DuplicateTransaction]


class DuplicateGroupPage(BaseModel):
    """Paginated list of unresolved duplicate groups."""
    groups: list[DuplicateGroup]
    total: int


class DuplicateStats(BaseModel):
    """Summary of pending duplicate work."""
    total_groups: int
    total_duplicate_transactions: int


class ResolveAction(str, Enum):
    CONFIRM_ALL = "confirm_all"          # All members are duplicates; keep lowest ID
    DISMISS_ALL = "dismiss_all"          # None are duplicates; add all pairs to exceptions
    CONFIRM_SELECTED = "confirm_selected"  # Only selected IDs are duplicates


class ResolveDuplicatesRequest(BaseModel):
    """Resolve one duplicate group."""
    transaction_ids: list[int]           # All IDs in the group
    action: ResolveAction
    selected_duplicate_ids: list[int] = []  # Used only for CONFIRM_SELECTED
