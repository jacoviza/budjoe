# Workflows — The Production Pipeline

## What This Folder Is

Three stages, each in its own folder. An agent enters one stage, does its work, and outputs to the next.

```
01-extract/  →  02-load/  →  [detect type]  →  03-transform/receipts/
  (extract)       (load)                     └─  03-transform/account-statements/
```

---

## Agent Routing

| Your Task | Input | Also Load | Output | Skills at This Stage |
|-----------|-------|-----------|--------|---------------------|
| Extract → Load | File from `01-extract/` | `../docs/what-to-look-for.md` | Parsed md document in `02-load/`. Original file is moved to `../parsed-files/` | `Read` (PDF) or `/glmocr` (images / scanned PDF) |
| Load → Transform (receipt) | `02-load/[slug].md` | `../docs/how-to-transform.md` | `03-transform/receipts/[YYYY-MM-DD-HHMMSS]-[commerce].md` | — |
| Load → Transform (bank statement) | `02-load/[slug].md` | `../docs/bank-statement-fields.md` + `../docs/how-to-transform-bank-statement.md` | `03-transform/account-statements/[period-end-YYYY-MM-DD]-[institution-slug]-[account-type].md` | — |

---

## Document Type Detection

Applied after Extract → Load, before Load → Transform. Read the `02-load/` file and score each type.

**A document is classified as the type that hits ≥2 signals first.**

### Bank statement signals

| Signal | Examples |
|--------|---------|
| Statement period phrase | "período", "del … al …", "from … to …", "periodo del estado" |
| Transaction table | Multiple rows with date + description + debit/credit columns |
| Financial institution header | "Banco", "Bank", "Asociación", "Credit Union", "Financiera" |
| Masked account number | `****1234`, `XXXX-4567`, `•••• 9999` |
| Balance keywords | "saldo anterior", "saldo actual", "balance forward", "opening balance" |
| Cut/payment date | "fecha de corte", "cut date", "fecha límite de pago", "payment due date" |

### Receipt / invoice signals

| Signal | Examples |
|--------|---------|
| Fiscal receipt indicator | NCF, comprobante fiscal, RNC |
| Single-transaction total | "total a pagar", "total amount due" with one sum |
| Merchant branding | Store name + address as header |
| Receipt keywords | "recibo", "factura", "ticket", "subtotal", "ITBIS" |

### Ambiguous documents

If neither or both types reach the ≥2 threshold: default to **receipt**, and prepend this line to the `02-load/` file before continuing:

```
> ⚠️ Document type uncertain — defaulted to receipt.
```

---

## Stage Details

### 01-extract/ — The Input

Pictures, screenshots, and PDFs of receipts, invoices, or bank statements pending parsing.

**File pattern:** `[slug].jpg`, `[slug].jpeg`, `[slug].png`, `[slug].pdf`

**Extraction logic by file type:**

| File type | Tool | Notes |
|-----------|------|-------|
| `.jpg` / `.jpeg` / `.png` | `/glmocr` | Always use OCR for images |
| `.pdf` | `Read` first | If text is readable, use it. If empty or garbled, fall back to `/glmocr` |

---

### 02-load/ — Raw extracted text

A md file containing the full extracted text of the document — unstructured, as-is from OCR or `Read`.

**File pattern:** `[slug].md`

The agent must NOT filter or interpret at this stage. Dump all readable text from the source document.

---

### 03-transform/ — Structured output

Two subfolders, one per document type. The agent reads the `02-load/` file, detects type, and writes to the correct subfolder.

#### 03-transform/receipts/

Structured 5-field table. Load `../docs/how-to-transform.md` for the exact format.

**File pattern:** `[YYYY-MM-DD-HHMMSS]-[commerce].md`

#### 03-transform/account-statements/

Structured statement with header + per-currency section(s) + transaction table(s).
Load `../docs/bank-statement-fields.md` and `../docs/how-to-transform-bank-statement.md`.

**File pattern:** `[period-end-YYYY-MM-DD]-[institution-slug]-[account-type].md`

---

## Pipeline Rules

1. **Flow is forward.** extract → load → detect → transform. No skipping stages.
2. **Each agent loads only what it needs.** See the routing table above.
3. **The parser does not have creative freedom.** It must return only the expected data.
4. **Detection happens at transform time**, not extract time. Always write to `02-load/` first.

---

## Where Skills Wire Into the Pipeline

```
01-extract/          02-load/           detect type        03-transform/
                    ┌─────────────┐                       ┌──────────────────────┐
                    │ /glmocr     │ ──→ receipt ────────→ │ receipts/            │
                    │  or Read    │                        └──────────────────────┘
                    └─────────────┘ ──→ bank statement ─→ ┌──────────────────────┐
                                                           │ account-statements/  │
                                                           └──────────────────────┘
```
