#!/usr/bin/env python3
"""
db/load_statement.py — Import an account-statement transform file into finance.db.

All statement files use YAML frontmatter format:
  ---
  financial_institution: BHD
  account_type: credit_card
  account_number_last4: 1234   (optional)
  account_product: AMEX SUMA   (optional)
  period_start: 2026-01-01
  period_end: 2026-01-31
  ---

  ## DOP

  currency: DOP
  account_balance: 11,052.53
  cut_date: 2026-01-31          (credit_card/loan/mortgage only)
  ...

  ### Transactions
  | date | merchant | debit | credit |
  ...

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
    parse_number,
    parse_tx_table,
    parse_yaml_kv,
    relative_path,
    statement_already_imported,
)


# ── Parsing ───────────────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter between the first pair of --- markers."""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return parse_yaml_kv(parts[1])


def split_h2_sections(text: str) -> list[tuple[str, str]]:
    """Split text into (heading, section_text) pairs at every ## heading."""
    pattern = re.compile(r"^## (.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections = []
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        start   = m.start()
        end     = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((heading, text[start:end]))
    return sections


def lines_before_h3(section_text: str) -> str:
    """Return lines that appear before the first ### heading (the summary block)."""
    result = []
    for line in section_text.splitlines():
        if line.startswith("###"):
            break
        if line.startswith("##"):
            continue  # skip the section heading itself
        result.append(line)
    return "\n".join(result)


def is_skip_section(heading: str) -> bool:
    """True for non-currency sections (Cuotas, installments, etc.)."""
    lower = heading.lower()
    return "cuotas" in lower or "installments" in lower


def extract_between(text: str, start_marker: str, end_marker: str) -> str:
    i = text.find(start_marker)
    if i == -1:
        return ""
    i += len(start_marker)
    j = text.find(end_marker, i)
    return text[i:j] if j != -1 else text[i:]


def parse_statement(text: str) -> tuple[dict, list[tuple[str, dict, list]]]:
    """
    Parse a YAML-frontmatter statement file.
    Returns (header_dict, [(currency, summary_dict, [tx_rows])]).
    """
    if not text.strip().startswith("---"):
        raise ValueError(
            "Statement file does not start with YAML frontmatter (---).\n"
            "All statement transforms must use the YAML frontmatter format.\n"
            "See ingestion/docs/how-to-transform-bank-statement.md for the correct format."
        )

    header = parse_frontmatter(text)

    # Body is everything after the closing ---
    body_start = text.find("---", text.find("---") + 3) + 3
    body = text[body_start:]

    sections = []
    for heading, section_text in split_h2_sections(body):
        if is_skip_section(heading):
            continue

        summary_block = lines_before_h3(section_text)
        summary = parse_yaml_kv(summary_block)

        currency = summary.get("currency", heading).strip()
        # Skip sections whose currency value looks like an installments marker
        if "(" in currency:
            continue

        if "### Transactions" in section_text:
            tx_block = extract_between(section_text, "### Transactions", "### Summary")
            txs = (
                []
                if not tx_block.strip() or "no transactions" in tx_block.lower()
                else parse_tx_table(tx_block)
            )
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
    conn.execute(
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
    )

    stmt_row = conn.execute(
        "SELECT id FROM account_statements WHERE source_file = ? AND currency = ?",
        (source_file, currency),
    ).fetchone()
    stmt_id = stmt_row["id"]

    inserted = 0
    for tx in txs:
        raw_debit  = tx["debit"]
        raw_credit = tx["credit"]
        if raw_debit is not None:
            amount, tx_type = raw_debit, "debit"
        else:
            amount, tx_type = raw_credit, "credit"

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
        header, sections = parse_statement(text)

        if not header.get("financial_institution") or not header.get("account_type"):
            print(f"ERROR: missing required header fields in {path.name}", file=sys.stderr)
            sys.exit(1)

        first_summary = sections[0][1] if sections else {}

        account_id = get_or_create_account(
            conn,
            institution          = header["financial_institution"],
            account_type         = header["account_type"],
            account_product      = header.get("account_product"),
            account_number_last4 = header.get("account_number_last4"),
            credit_limit         = parse_number(first_summary.get("credit_limit")),
            minimum_payment      = parse_number(first_summary.get("minimum_payment")),
            interest_rate_annual = first_summary.get("interest_rate_annual"),
            apy                  = first_summary.get("apy"),
        )

        print(f"Importing: {path.name}")
        for currency, summary, txs in sections:
            insert_currency_section(conn, account_id, header, currency, summary, txs, src)

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
