"""
Database connection and utilities for the Finance Control Panel.
Re-imports shared utilities from the db/ directory via sys.path.
"""

import sys
from pathlib import Path

# Add db/ to sys.path so we can import lib.py
WORKSPACE_ROOT = Path(__file__).parent.parent.parent  # web/backend/ → repo root
DB_DIR = WORKSPACE_ROOT / "db"
sys.path.insert(0, str(DB_DIR))

# Now we can import from lib.py
from lib import get_connection, get_or_create_account, get_or_create_cash_account

__all__ = [
    "WORKSPACE_ROOT",
    "DB_DIR",
    "get_connection",
    "get_or_create_account",
    "get_or_create_cash_account",
]
