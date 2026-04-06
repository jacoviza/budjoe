#!/usr/bin/env python3
"""
db/load_statement.py — Import an account-statement transform file into finance.db.

Supports two transform formats:
  Format A — ## Header section with | Field | Value | table (BHD, early Scotiabank)
  Format B — YAML frontmatter between --- markers (Scotiabank Mar 2026+)

Usage:
    python db/load_statement.py <path-to-statement-transform.md>
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import (
    get_connection,
    get_or_create_account,
    now_iso,
    parse_kv_table,
    parse_number,
    parse_tx_table,
    parse_yaml_kv,
    relative_path,
    statement_already_imported,
)


# ── Section splitter ──────────────────────────────────────────────────────────

def split_h2_sections(text: str) -> list[tuple[str, str]]:
    """
    Split text into (heading, section_text) pairs at every ## heading.
    section_text includes the heading line itself.
    """
    pattern = re.compile(r"^## (.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections = []
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        start   = m.start()
        end     = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((heading, text[start:end]))
    return sections


def extract_between(text: str, start_marker: str, end_marker: str) -> str:
    """Return text between start_marker and end_marker (exclusive). Case-sensitive."""
    i = text.find(start_marker)
    if i == -1:
        return ""
    i += len(start_marker)
    j = text.find(end_marker, i)
    return text[i:j] if j != -1 else text[i:]


def extract_after(text: str, marker: str) -> str:
    i = text.find(marker)
    return text[i + len(marker):] if i != -1 else ""


# ── Format A ──────────────────────────────────────────────────────────────────

def parse_format_a(text: str) -> tuple[dict, list[tuple[str, dict, list]]]:
    """
    Parse Format A (## Header with | Field | Value | table).
    Returns (header_dict, [(currency, summary_dict, [tx_rows])])
    """
    # Header
    header_block = extract_between(text, "## Header", "## ")
    header = parse_kv_table(header_block)

    sections = []
    for heading, section_text in split_h2_sections(text):
        if heading.lower() == "header":
            continue

        currency = heading.strip()  # "DOP", "USD", etc.

        # Summary is between ### Summary and ### Transactions
        summary_block = extract_between(section_text, "### Summary", "### Transactions")
        summary = parse_kv_table(summary_block)

        # Transactions are after ### Transactions
        tx_block = extract_after(section_text, "### Transactions")
        txs = parse_tx_table(tx_block) if tx_block.strip() else []

        sections.append((currency, summary, txs))

    return header, sections


# ── Format B ──────────────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> dict:
    """Extract and parse YAML frontmatter between the first pair of --- markers."""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return parse_yaml_kv(parts[1])


def lines_before_h3(section_text: str) -> str:
    """Return lines in section_text that appear before the first ### heading."""
    result = []
    for line in section_text.splitlines():
        if line.startswith("###"):
            break
        # skip the ## heading line itself
        if line.startswith("##"):
            continue
        result.append(line)
    return "\n".join(result)


def is_skip_section(heading: str) -> bool:
    """True for non-currency sections like Cuotas that should be ignored."""
    lower = heading.lower()
    return "cuotas" in lower or "installments" in lower


def parse_format_b(text: str) -> tuple[dict, list[tuple[str, dict, list]]]:
    """
    Parse Format B (YAML frontmatter + bare key:value summaries).
    Returns (header_dict, [(currency, summary_dict, [tx_rows])])
    """
    header = parse_frontmatter(text)

    # Normalise card_product / card_last4 → account_product / account_number_last4
    if "card_product" in header and "account_product" not in header:
        header["account_product"] = header.pop("card_product")
    if "card_last4" in header and "account_number_last4" not in header:
        header["account_number_last4"] = header.pop("card_last4")

    # Work on the body after the closing ---
    body_start = text.find("---", text.find("---") + 3) + 3
    body = text[body_start:]

    sections = []
    for heading, section_text in split_h2_sections(body):
        if is_skip_section(heading):
            continue

        # Summary: bare key:value lines before the first ### heading
        summary_block = lines_before_h3(section_text)
        summary = parse_yaml_kv(summary_block)

        # Currency comes from the summary block; fall back to the heading
        currency = summary.get("currency", heading).strip()
        # Guard: skip if currency value looks like an installments marker
        if "(" in currency:
            continue

        # Transactions: between ### Transactions and ### Summary (period totals)
        if "### Transactions" in section_text:
            tx_block = extract_between(section_text, "### Transactions", "### Summary")
            if not tx_block.strip() or "no transactions" in tx_block.lower():
                txs = []
            else:
                txs = parse_tx_table(tx_block)
        else:
            txs = []

        sections.append((currency, summary, txs))

    return header, sections


# ── DB writer ─────────────────────────────────────────────────────────────────

def insert_currency_section(
    conn,
    account_id: int,
    header: dict,
    currency: str,
    summary: dict,
    txs: list[dict],
    source_file: str,
) -> None:
    """Insert one account_statements row + its transactions."""

    stmt_id = conn.execute(
        """
        INSERT OR IGNORE INTO account_statements (
            account_id, period_start, period_end, currency, account_balance,
            cut_date, balance_at_cut, payment_due_date, source_file
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            account_id,
            header.get("period_start"),
            header.get("period_end"),
            currency,
            parse_number(summary.get("account_balance")),
            summary.get("cut_date"),
            parse_number(summary.get("balance_at_cut")),
            summary.get("payment_due_date"),
            source_file,
        ),
    ).lastrowid

    # lastrowid is 0 on IGNORE — fetch the real id
    if not stmt_id:
        stmt_id = conn.execute(
            "SELECT id FROM account_statements WHERE source_file = ? AND currency = ?",
            (source_file, currency),
        ).fetchone()["id"]

    inserted = 0
    for tx in txs:
        raw_debit  = tx["debit"]
        raw_credit = tx["credit"]
        if raw_debit is not None:
            amount  = raw_debit
            tx_type = "debit"
        else:
            amount  = raw_credit
            tx_type = "credit"

        result = conn.execute(
            """
            INSERT OR IGNORE INTO transactions (
                account_id, statement_id,
                date, merchant, currency,
                debit, credit, amount, tx_type,
                source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_id, stmt_id,
                tx["date"], tx["merchant"], currency,
                raw_debit, raw_credit, amount, tx_type,
                source_file,
            ),
        )
        inserted += result.rowcount

    print(f"    {currency}: {inserted} transaction(s) inserted")


# ── Loader ────────────────────────────────────────────────────────────────────

def load_statement(filepath: str) -> None:
    path = Path(filepath).resolve()
    src  = relative_path(path)

    with get_connection() as conn:
        if statement_already_imported(conn, src):
            print(f"Already imported: {src}. Skipping.")
            return

        text = path.read_text(encoding="utf-8")

        if text.strip().startswith("---"):
            header, sections = parse_format_b(text)
        else:
            header, sections = parse_format_a(text)

        if not header.get("financial_institution") or not header.get("account_type"):
            print(
                f"ERROR: could not parse header from {path.name}", file=sys.stderr
            )
            sys.exit(1)

        # Pull type-specific fields from the first currency section's summary
        first_summary = sections[0][1] if sections else {}

        account_id = get_or_create_account(
            conn,
            institution         = header["financial_institution"],
            account_type        = header["account_type"],
            account_product     = header.get("account_product"),
            account_number_last4= header.get("account_number_last4"),
            credit_limit        = parse_number(first_summary.get("credit_limit")),
            minimum_payment     = parse_number(first_summary.get("minimum_payment")),
            interest_rate_annual= first_summary.get("interest_rate_annual"),
            apy                 = first_summary.get("apy"),
        )

        print(f"Importing: {path.name}")
        for currency, summary, txs in sections:
            insert_currency_section(
                conn, account_id, header, currency, summary, txs, src
            )

        conn.commit()

    print(f"Done: {path.name}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: python db/load_statement.py <statement-transform.md>",
            file=sys.stderr,
        )
        sys.exit(1)
    load_statement(sys.argv[1])


if __name__ == "__main__":
    main()
