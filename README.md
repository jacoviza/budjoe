# Personal Finance Workspace

An agent-driven ELT pipeline that converts receipt and invoice photos into structured transaction records.

---

## How It Works

Drop an image or PDF into the conversation. The pipeline runs automatically:

```
01-extract/  →  02-load/  →  03-transform/  →  parsed-files/
  (raw file)    (OCR text)    (structured md)    (archived original)
```

| Stage | Folder | What Happens |
|-------|--------|--------------|
| **Extract** | `ingestion/workflows/01-extract/` | Raw image/PDF lands here |
| **Load** | `ingestion/workflows/02-load/` | `/glmocr` parses it into readable markdown |
| **Transform** | `ingestion/workflows/03-transform/` | Key fields extracted into a structured table |
| **Archive** | `ingestion/parsed-files/` | Original file moved here after successful parse |

---

## Output Format

Each transformed file is a markdown table with five fields:

| Field | Description |
|-------|-------------|
| `datetime` | Date and time of the transaction |
| `merchant` | Name of the merchant |
| `subtotal` | Amount before taxes |
| `total` | Total amount paid |
| `taxes` | ITBIS, IVA, or equivalent |

**Example:**

```
| Field    | Value               |
|----------|---------------------|
| datetime | 2026-03-04-13:45:23 |
| merchant | Supermercados Bravo |
| subtotal | 1000.00             |
| total    | 1180.00             |
| taxes    | 180.00              |
```

---

## Naming Conventions

| Location | Pattern | Example |
|----------|---------|---------|
| `02-load/` | `[slug].md` | `IMG_20251001_205531.md` |
| `03-transform/` | `[YYYY-MM-DD-HHMMSS]-[commerce].md` | `2025-10-01-210440-supermercados-nacional.md` |
| `parsed-files/` | `[YYYY-MM-DD]-[slug]-parsed.[ext]` | `2025-10-01-IMG_20251001_205531-parsed.jpg` |

---

## Tools

| Tool | Purpose |
|------|---------|
| `/glmocr` | OCR skill — extracts text from receipt/invoice images |

---

## Project Structure

```
finanzas/
├── CLAUDE.md               ← Workspace map and rules (always loaded)
├── CONTEXT.md              ← Task router
├── README.md               ← This file
└── ingestion/
    ├── CONTEXT.md
    ├── docs/
    │   ├── what-to-look-for.md   ← Fields to extract
    │   └── how-to-transform.md   ← Transform output spec
    └── workflows/
        ├── CONTEXT.md
        ├── 01-extract/     ← (gitignored) Raw files pending parse
        ├── 02-load/        ← (gitignored) OCR output markdown
        └── 03-transform/   ← (gitignored) Structured transaction files
```
