```
██████╗ ██╗   ██╗██████╗      ██╗ ██████╗ ███████╗
██╔══██╗██║   ██║██╔══██╗     ██║██╔═══██╗██╔════╝
██████╔╝██║   ██║██║  ██║     ██║██║   ██║█████╗
██╔══██╗██║   ██║██║  ██║██   ██║██║   ██║██╔══╝
██████╔╝╚██████╔╝██████╔╝╚█████╔╝╚██████╔╝███████╗
╚═════╝  ╚═════╝ ╚═════╝  ╚════╝  ╚═════╝ ╚══════╝
```

Personal finance workspace — ingestion, storage, and control panel in one place.

---

## Overview

Three subsystems that work together:

| Layer | Folder | What It Does |
|-------|--------|--------------|
| **Ingestion** | `ingestion/` | OCR pipeline — turns receipt/invoice photos and bank statement PDFs into structured markdown |
| **Database** | `db/` | SQLite persistence — versioned migrations, importers for all document types |
| **Web UI** | `web/` | Finance Control Panel — React + FastAPI for browsing accounts, reviewing transactions, and resolving duplicates |
| **Bank Notifications** | `bank-notifications/` | Gmail transactional emails → pending transactions → DB |

---

## Quick Start

**Terminal 1 — Backend (FastAPI, port 8000)**
```bash
cd web/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Terminal 2 — Frontend (Vite, port 5173)**
```bash
cd web/frontend
pnpm install
pnpm dev
```

Open [http://localhost:5173](http://localhost:5173).

> First run: apply migrations before starting.
> ```bash
> python db/migrate.py
> ```

---

## Web Control Panel

Five pages covering the full transaction lifecycle:

| Page | Route | What You Can Do |
|------|-------|-----------------|
| **Accounts** | `/accounts` | Grid view of all accounts with latest DOP balances |
| **Account Detail** | `/accounts/:id` | Browse statements, paginated transactions, inline editing |
| **Notifications** | `/notifications` | Review and bulk approve/reject pending bank notification transactions |
| **Duplicates** | `/duplicates` | Detect suspected duplicates and mark as duplicate or exception |
| **Actions** | `/actions` | Run DB migrations, load pending files, list unprocessed transforms |

### Transaction Management
- Inline cell editing — merchant, description, date, amount, type
- Move a transaction to a different account
- Full edit modal for complex changes

---

## Data Flow

```
Receipt / Invoice photo
    → ingestion/01-extract/
    → /glmocr (OCR)
    → ingestion/02-load/
    → structured markdown
    → ingestion/03-transform/receipts/
    → python db/load_receipt.py
    → finance.db

Bank Statement PDF
    → ingestion/01-extract/
    → Read (native text)
    → ingestion/02-load/
    → structured markdown
    → ingestion/03-transform/account-statements/
    → python db/load_statement.py
    → finance.db

Gmail bank notification
    → bank-notifications/01-transactions-to-load/
    → python db/load_notification.py
    → finance.db (status: pending)
    → Notifications page → approve/reject
```

All three paths end up in the same SQLite database, browseable through the web UI.

---

## Database Scripts

| Script | Purpose |
|--------|---------|
| `db/migrate.py` | Apply versioned SQL migrations |
| `db/load_receipt.py <file>` | Import a structured receipt transform |
| `db/load_statement.py <file>` | Import a structured bank statement transform |
| `db/load_notification.py` | Batch-load pending notification files into DB |
| `db/detect_duplicates.py` | CLI tool for interactive duplicate resolution |

All loaders are idempotent — re-running on an already-imported file prints `Already imported. Skipping.` and exits 0.

**Schema changes:** add a new numbered file to `db/migrations/` (e.g. `007_add_notes.sql`) and re-run `python db/migrate.py`. Never edit already-applied migration files.

---

## Ingestion Pipeline

Drop an image or PDF into the conversation. The pipeline runs automatically:

```
01-extract/  →  02-load/  →  03-transform/  →  parsed-files/
  (raw file)    (OCR text)    (structured md)    (archived original)
```

| File Type | Primary Tool | Fallback |
|-----------|-------------|---------|
| `.jpg` / `.jpeg` / `.png` | `/glmocr` | — |
| `.pdf` | `Read` (native text) | `/glmocr` if garbled |

### Transform Output Fields

| Field | Description |
|-------|-------------|
| `datetime` | Date and time of the transaction |
| `merchant` | Name of the merchant |
| `subtotal` | Amount before taxes |
| `total` | Total amount paid |
| `taxes` | ITBIS, IVA, or equivalent |

---

## Project Structure

```
personal-finances/
├── CLAUDE.md                          ← Workspace map (always loaded)
├── CONTEXT.md                         ← Task router
├── README.md                          ← This file
│
├── db/                                ← SQLite persistence layer
│   ├── finance.db                     ← Database (auto-created)
│   ├── migrations/                    ← Versioned SQL (001–006)
│   ├── migrate.py                     ← Migration runner
│   ├── lib.py                         ← Shared DB utilities
│   ├── load_statement.py              ← Bank statement importer
│   ├── load_receipt.py                ← Receipt importer
│   ├── load_notification.py           ← Bank notification importer
│   └── detect_duplicates.py          ← Duplicate detection CLI
│
├── web/                               ← Finance Control Panel
│   ├── CONTEXT.md
│   ├── README.md
│   ├── DARK_MODE_GUIDE.md
│   ├── backend/                       ← FastAPI (port 8000)
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── requirements.txt
│   │   └── routers/                   ← accounts, transactions, notifications, duplicates, actions
│   └── frontend/                      ← React + TypeScript + Vite (port 5173)
│       └── src/
│           ├── api/                   ← Typed API client
│           ├── components/            ← Layout + transaction components
│           ├── pages/                 ← Accounts, Notifications, Duplicates, Actions
│           ├── types/                 ← TypeScript interfaces
│           └── context/               ← ThemeContext (dark mode)
│
├── bank-notifications/                ← Gmail → DB pipeline
│   ├── CONTEXT.md
│   ├── rules.md                       ← Sender → institution mapping
│   ├── 01-transactions-to-load/       ← Pending files
│   └── 02-loaded-transactions/        ← Processed files (audit trail)
│
└── ingestion/                         ← Receipt / statement OCR pipeline
    ├── CONTEXT.md
    ├── docs/                          ← Field specs and transform rules
    └── workflows/
        ├── 01-extract/                ← Raw files (gitignored)
        ├── 02-load/                   ← OCR output (gitignored)
        └── 03-transform/
            ├── receipts/
            └── account-statements/
```

---

## Naming Conventions

| Content | Pattern | Example |
|---------|---------|---------|
| Receipt transform | `[YYYY-MM-DD-HHMMSS]-[commerce].md` | `2026-03-10-210440-supermercados-nacional.md` |
| Statement transform | `[period-end-YYYY-MM-DD]-[institution-slug]-[account-type].md` | `2026-03-31-banco-popular-credit-card.md` |
| Bank notification | `[YYYY-MM-DD-HHMMSS]-[merchant-slug].md` | `2026-04-04-102300-supermercados-nacional.md` |

---

## Further Reading

| File | When to read it |
|------|-----------------|
| `web/CONTEXT.md` | Starting work on the web UI |
| `web/README.md` | Web architecture, components, constraints |
| `web/DARK_MODE_GUIDE.md` | Dark mode tokens and styling conventions |
| `bank-notifications/CONTEXT.md` | Processing Gmail bank notifications |
| `ingestion/CONTEXT.md` | Parsing receipts or bank statements |
