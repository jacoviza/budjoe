# Acme DevRel — Workspace Map

<!--
=======================================================================
TEACHING NOTE: This is LAYER 1 — THE MAP.

CLAUDE.md is auto-loaded into every conversation. It's always in context.
That makes it prime real estate. Use it for:

  1. Folder structure (so the agent always knows where things live)
  2. ID systems & naming conventions (so files land in the right place)
  3. File placement rules (so nothing gets lost)
  4. Quick navigation table (task → workspace)

Do NOT put:
  - Detailed instructions (those go in workspace CONTEXT.md files)
  - Voice/style guides (those go in docs/)
  - Pipeline details (those go in workflows/CONTEXT.md)

Keep it under 200 lines. Every line here costs tokens in EVERY conversation.
=======================================================================
-->

## What This Is

A workspace system for my personal finances. Ingestion, Tracking, and Budgeting — each in its own silo. An agent drops into a workspace, reads its CONTEXT.md, does its work, and exits.

**CONTEXT.md** (top-level) routes you to the right workspace. This file is the map.

---

## Folder Structure

```
finances-workspace/
├── CLAUDE.md                       ← You are here (always loaded)
├── CONTEXT.md                      ← Task router
│
├── db/                             ← SQLite persistence layer
│   ├── migrations/                 ← Versioned SQL migration files
│   │   └── 001_initial_schema.sql
│   ├── migrate.py                  ← Migration runner
│   ├── lib.py                      ← Shared DB utilities
│   ├── load_statement.py           ← Statement importer
│   ├── load_receipt.py             ← Receipt importer
│   └── finance.db                  ← SQLite database (auto-created)
│
└── ingestion/                      ← Parses receipts, invoices, and bank statements
    ├── CONTEXT.md
    ├── docs/
    │   ├── what-to-look-for.md
    │   ├── how-to-transform.md
    │   ├── bank-statement-fields.md
    │   └── how-to-transform-bank-statement.md
    ├── workflows/
    │   ├── CONTEXT.md              ← Pipeline routing + detection rules
    │   ├── 01-extract/             ← Raw files pending parsing
    │   ├── 02-load/                ← Raw extracted text (all document types)
    │   └── 03-transform/
    │       ├── receipts/           ← Structured receipt/invoice outputs
    │       └── account-statements/ ← Structured bank statement outputs
    └── parsed-files                ← Original files after successful parsing
 
```

---

## Quick Navigation

| Want to... | Go here |
|------------|---------|
| **Parse a receipt or invoice** | `ingestion/CONTEXT.md` |
| **Parse a bank/account statement** | `ingestion/CONTEXT.md` |
| **Persist a transform to the DB** | Run `python db/load_statement.py <file>` or `python db/load_receipt.py <file>` |
| **Apply schema migrations** | Run `python db/migrate.py` |

---



<!--
TEACHING NOTE: Cross-workspace flow is ONE-WAY.
writing-room outputs feed into production inputs.
Both feed into community. But community never feeds back.

This is important because it means an agent in writing-room
never needs to know about production's pipeline stages.
-->

---

## ID & Naming Conventions

<!--
TEACHING NOTE: Naming conventions belong in CLAUDE.md because
they apply EVERYWHERE. Any agent creating a file needs these rules,
regardless of which workspace it's in.
-->

| Content Type | Pattern | Example |
|-------------|---------|---------|
| Receipt / invoice transform | `[YYYY-MM-DD-HHMMSS]-[commerce].md` | `2026-03-10-210440-supermercados-nacional.md` |
| Bank statement transform | `[period-end-YYYY-MM-DD]-[institution-slug]-[account-type].md` | `2026-03-31-banco-popular-credit-card.md` |

---

## File Placement Rules

### Ingestion
- **Raw files (any type):** `ingestion/workflows/01-extract/[slug].[png|jpg|jpeg|pdf]`
- **Raw extracted text:** `ingestion/workflows/02-load/[slug].md`
- **Structured receipts:** `ingestion/workflows/03-transform/receipts/[YYYY-MM-DD-HHMMSS]-[commerce].md`
- **Structured bank statements:** `ingestion/workflows/03-transform/account-statements/[period-end-YYYY-MM-DD]-[institution-slug]-[account-type].md`
- **Processed originals:** `ingestion/parsed-files/[YYYY-MM-DD]-[slug]-parsed.[png|jpg|jpeg|pdf]`

---

## Token Management

<!--
TEACHING NOTE: This section is the #1 thing people miss.
It tells agents what NOT to load. Without this, agents will
try to read everything and blow their context window.
-->

**Each workspace is siloed.** Don't load everything.

- Parsing a receipt or invoice? → Load `ingestion/docs/what-to-look-for.md`.
- Parsing a bank statement? → Load `ingestion/docs/bank-statement-fields.md`.

The CONTEXT.md files tell you what to load for each task. Trust them.

---

## Auto-Ingestion Trigger

When the user attaches an image or PDF (jpg, jpeg, png, pdf) in the conversation:
1. Copy the file to `ingestion/workflows/01-extract/[original-filename]`
2. Immediately run the full pipeline without waiting for further instructions:
   - Extract → see extraction rules below
   - Load → write raw extracted text to `ingestion/workflows/02-load/[slug].md`
   - Detect document type using signals in `ingestion/workflows/CONTEXT.md`
   - Transform (receipt) → write to `ingestion/workflows/03-transform/receipts/[YYYY-MM-DD-HHMMSS]-[commerce].md`
   - Transform (bank statement) → write to `ingestion/workflows/03-transform/account-statements/[period-end]-[institution-slug]-[account-type].md`
   - Persist to DB → `python db/load_statement.py <transform-file>` or `python db/load_receipt.py <transform-file>`
   - Move original to `ingestion/parsed-files/[YYYY-MM-DD]-[slug]-parsed.[ext]`

### DB Persistence

`db/finance.db` is created automatically on first `python db/migrate.py`. The loaders are idempotent — re-running on an already-imported file prints "Already imported. Skipping." and exits 0.

**Receipts:** the loader prompts you to select which account was used. If no real accounts exist yet, it defaults to a virtual cash account.

**Schema changes:** add a new numbered file to `db/migrations/` (e.g. `002_add_notes.sql`) and re-run `python db/migrate.py`. Never edit already-applied migration files.

### Extraction Rules by File Type

| File type | Primary tool | Fallback |
|-----------|-------------|---------|
| `.jpg` / `.jpeg` / `.png` | `/glmocr` | — |
| `.pdf` | `Read` (native text extraction) | `/glmocr` if output is empty or garbled |

For PDFs: attempt `Read` first. If the extracted text is readable, use it. If the output is empty, garbled, or clearly image-based, fall back to `/glmocr`.

---

## Skills & Tools Available

<!--
TEACHING NOTE: This section maps which skills and MCPs are
available at the SYSTEM level. Individual workspaces and pipeline
stages reference specific tools in their own CONTEXT.md files.

Think of this as the "installed tools" list. The workspace CONTEXT
files are the "when to use them" instructions.

You can wire up to 15 skills per workspace. They don't all live here —
workspace CONTEXT.md files reference them at the point of use.
-->

| Tool | Type | Used In |
|------|------|---------|
| `/glmocr` | Skill | OCR for image-based receipts/invoices (jpg, jpeg, png) and scanned PDFs |
| `Read` | Built-in tool | Native text extraction for digital PDFs (try first before glmocr) |

See each workspace's CONTEXT.md for when and how these tools get invoked.
