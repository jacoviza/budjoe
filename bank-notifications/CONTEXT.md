# Bank Notifications

Scans Gmail for transactional bank push emails, extracts transaction data into intermediate files, and loads them into the finance DB as pending-review transactions. Approval is a separate future workflow.

---

## Folder Structure

```
bank-notifications/
├── CONTEXT.md              ← You are here
├── rules.md                ← User-editable sender → institution mappings
└── transactions/           ← Pending and imported transaction files
```

---

## Commands

| Task | Command |
|------|---------|
| **Scan Gmail and write pending files** | Read `rules.md`, use Gmail MCP tools, write files to `transactions/` |
| **Load pending files to DB** | `python db/load_notification.py` |
| **Apply DB migration (first-time setup)** | `python db/migrate.py` |

---

## Scan Workflow (Agent Instructions)

1. Read `bank-notifications/rules.md`.
2. For each rule, call `gmail_search_messages` with the provided Gmail query.
3. For each message returned, call `gmail_read_message` to get the full body.
4. Before writing, scan `bank-notifications/transactions/*.md` — check each file's `email_id` frontmatter field. **Skip if a match is found** (deduplication).
5. Extract transaction fields from the email body using the extraction hints in `rules.md`.
6. Write a new `.md` file to `bank-notifications/transactions/` using the naming convention: `[YYYY-MM-DD-HHMMSS]-[merchant-slug].md`.
7. Set `status: pending` in the frontmatter.

### File Format

```markdown
---
status: pending
email_id: <gmail_message_id>
email_from: notificaciones@bhd.com.do
email_subject: Transacción con tu tarjeta BHD
email_date: 2026-04-04T10:23:00
institution: BHD
account_type: credit_card
account_number_last4: 4449
---

| Field    | Value |
|----------|-------|
| datetime | 2026-04-04 10:23:00 |
| merchant | SUPERMERCADOS NACIONAL |
| amount   | 2,314.45 |
| currency | DOP |
| tx_type  | debit |
```

### Merchant Slug (filename)
- Lowercase, replace spaces and special characters with hyphens, truncate to 40 characters
- `SUPERMERCADOS NACIONAL` → `supermercados-nacional`
- Final filename example: `2026-04-04-102300-supermercados-nacional.md`

---

## File Status Values

| Status | Set by | Meaning |
|--------|--------|---------|
| `pending` | Scanner | Written to disk, not yet loaded to DB |
| `imported` | Loader | Successfully inserted into `transactions` table |

---

## DB Status Values (`notification_status` column)

| Value | Meaning |
|-------|---------|
| `pending` | Loaded from email scan, awaiting user review |
| `approved` | Approved by user (future workflow) |
| `rejected` | Rejected by user (future workflow) |

---

## Deduplication

- **Scanner-level:** Before writing, check `email_id` in all existing `*.md` files in `transactions/`. Skip if found.
- **DB-level:** `load_notification.py` uses `source_file` (workspace-root-relative path) as idempotency key — same pattern as receipts.

---

## Hard Rules

1. Never modify `db/lib.py`, `db/load_receipt.py`, or `db/load_statement.py`.
2. All transactions loaded here enter the DB with `notification_status = 'pending'`. Approval is a separate future workflow.
3. Never delete files from `transactions/` — they are the permanent audit trail.
4. Always check `email_id` against existing files before writing a new one.
