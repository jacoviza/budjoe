"""
Actions API endpoints - runs workspace commands and filesystem scans.
"""

import subprocess
import sys
from pathlib import Path
from fastapi import APIRouter
import yaml

from db import get_connection, WORKSPACE_ROOT
from models import ActionResult, PendingFilesResult

router = APIRouter()


def _run_subprocess(cmd: list, timeout: int = 60) -> ActionResult:
    """
    Safely run a subprocess with the current Python interpreter.
    Never use shell=True.
    """
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE_ROOT),
        timeout=timeout,
    )
    return ActionResult(
        success=result.returncode == 0,
        stdout=result.stdout,
        stderr=result.stderr,
        return_code=result.returncode,
    )


@router.post("/migrate")
def run_migrate() -> ActionResult:
    """Run: python db/migrate.py"""
    python = sys.executable
    return _run_subprocess([python, str(WORKSPACE_ROOT / "db" / "migrate.py")])


@router.get("/migrate/status")
def get_migrate_status() -> ActionResult:
    """Run: python db/migrate.py --status"""
    python = sys.executable
    return _run_subprocess(
        [python, str(WORKSPACE_ROOT / "db" / "migrate.py"), "--status"]
    )


@router.post("/load-notifications")
def run_load_notifications() -> ActionResult:
    """Run: python db/load_notification.py"""
    python = sys.executable
    return _run_subprocess([python, str(WORKSPACE_ROOT / "db" / "load_notification.py")])


@router.get("/pending-files")
def get_pending_files() -> PendingFilesResult:
    """
    Scan filesystem for unprocessed files:
    - Bank notifications with status: pending
    - Receipt transforms not yet imported
    - Statement transforms not yet imported
    """
    with get_connection() as conn:
        # Load imported receipts and statements
        imported_receipts = set()
        imported_statements = set()

        receipt_rows = conn.execute(
            "SELECT DISTINCT source_file FROM transactions WHERE statement_id IS NULL AND source_file LIKE '%/receipts/%'"
        ).fetchall()
        imported_receipts.update(r["source_file"] for r in receipt_rows)

        stmt_rows = conn.execute(
            "SELECT DISTINCT source_file FROM account_statements"
        ).fetchall()
        imported_statements.update(r["source_file"] for r in stmt_rows)

    # Scan bank notifications pending files
    pending_notifications = []
    notif_dir = WORKSPACE_ROOT / "bank-notifications" / "01-transactions-to-load"
    if notif_dir.exists():
        for md_file in notif_dir.glob("*.md"):
            # Check if status: pending in frontmatter
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.startswith("---"):
                        # Extract YAML frontmatter
                        _, yaml_block, _ = content.split("---", 2)
                        data = yaml.safe_load(yaml_block)
                        if data and data.get("status") == "pending":
                            pending_notifications.append(md_file.name)
            except Exception:
                # Skip files that can't be parsed
                pass

    # Scan receipt transforms
    pending_receipts = []
    receipt_dir = WORKSPACE_ROOT / "ingestion" / "workflows" / "03-transform" / "receipts"
    if receipt_dir.exists():
        for md_file in receipt_dir.glob("*.md"):
            # Check if this file has been imported
            relative = str(md_file.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
            if relative not in imported_receipts:
                pending_receipts.append(md_file.name)

    # Scan statement transforms
    pending_statements = []
    stmt_dir = (
        WORKSPACE_ROOT / "ingestion" / "workflows" / "03-transform" / "account-statements"
    )
    if stmt_dir.exists():
        for md_file in stmt_dir.glob("*.md"):
            # Check if this file has been imported
            relative = str(md_file.relative_to(WORKSPACE_ROOT)).replace("\\", "/")
            if relative not in imported_statements:
                pending_statements.append(md_file.name)

    return PendingFilesResult(
        notification_files=sorted(pending_notifications),
        receipt_transforms=sorted(pending_receipts),
        statement_transforms=sorted(pending_statements),
    )
