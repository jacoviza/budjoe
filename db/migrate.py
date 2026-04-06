#!/usr/bin/env python3
"""
db/migrate.py — SQLite migration runner.

Usage:
    python db/migrate.py            # apply all pending migrations
    python db/migrate.py --status   # show applied vs pending
"""

import re
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "finance.db"
MIGRATIONS_DIR = Path(__file__).parent / "migrations"

BOOTSTRAP_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    INTEGER PRIMARY KEY,
    filename   TEXT    NOT NULL,
    applied_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def bootstrap(conn: sqlite3.Connection) -> None:
    """Ensure schema_migrations table exists before anything else."""
    conn.executescript(BOOTSTRAP_DDL)
    conn.commit()


def applied_versions(conn: sqlite3.Connection) -> set[int]:
    return {
        row["version"]
        for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
    }


def parse_version(filename: str) -> int | None:
    """Extract leading integer from filename, e.g. '001_foo.sql' → 1."""
    m = re.match(r"^(\d+)", filename)
    return int(m.group(1)) if m else None


def collect_migrations() -> list[tuple[int, Path]]:
    """Return sorted list of (version, path) for all .sql files in migrations/."""
    result = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        version = parse_version(path.name)
        if version is not None:
            result.append((version, path))
    return result


def apply_migration(conn: sqlite3.Connection, version: int, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    try:
        conn.executescript(sql)          # executescript auto-commits
        conn.execute(
            "INSERT INTO schema_migrations (version, filename) VALUES (?, ?)",
            (version, path.name),
        )
        conn.commit()
        print(f"  Applied  {path.name}")
    except Exception as exc:
        conn.rollback()
        print(f"  ERROR applying {path.name}: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_migrate(conn: sqlite3.Connection) -> None:
    bootstrap(conn)
    applied = applied_versions(conn)
    migrations = collect_migrations()

    if not migrations:
        print("No migration files found in db/migrations/")
        return

    pending = [(v, p) for v, p in migrations if v not in applied]
    if not pending:
        print("All migrations already applied.")
        return

    print(f"Applying {len(pending)} migration(s)…")
    for version, path in pending:
        apply_migration(conn, version, path)
    print("Done.")


def cmd_status(conn: sqlite3.Connection) -> None:
    bootstrap(conn)
    applied = applied_versions(conn)
    migrations = collect_migrations()

    if not migrations:
        print("No migration files found in db/migrations/")
        return

    print(f"{'Version':<10} {'Status':<12} Filename")
    print("-" * 50)
    for version, path in migrations:
        status = "applied" if version in applied else "pending"
        print(f"{version:<10} {status:<12} {path.name}")


def main() -> None:
    args = sys.argv[1:]
    with get_connection() as conn:
        if "--status" in args:
            cmd_status(conn)
        else:
            cmd_migrate(conn)


if __name__ == "__main__":
    main()
