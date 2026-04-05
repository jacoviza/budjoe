# Ingestion

<!--
=======================================================================
TEACHING NOTE: This workspace demonstrates the PIPELINE pattern.

Production has two levels of CONTEXT.md:
  1. This file (workspace entry point) — routes to docs or workflows
  2. workflows/CONTEXT.md (pipeline entry point) — routes to stages

This is the most complex workspace in the template. It shows:
  - Sub-routing (workspace CONTEXT → pipeline CONTEXT)
  - Reference docs separate from workflow
  - Stage-specific tool integration
  - Creative freedom within constraints (specs vs builds)
=======================================================================
-->

## What This Workspace Is

The transformation hub. Screenshots, receipts and invoice photos and pdfs are transformed into structured transaction md files.


---

## Where to Go

| You Want To... | Go Here |
|----------------|---------|
| **Understand the pipeline** | `workflows/CONTEXT.md` |
| **Look up what to extract from receipts/invoices** | `docs/what-to-look-for.md` |
| **Look up what to extract from bank statements** | `docs/bank-statement-fields.md` |
| **Look up the receipt transform format** | `docs/how-to-transform.md` |
| **Look up the bank statement transform format** | `docs/how-to-transform-bank-statement.md` |

**Don't read everything.** Identify your task, load only what you need.

---

## Folder Structure

```
ingestion/                      ← Parses receipts, invoices, and bank statements from photos, screenshots or PDFs
├── CONTEXT.md
├── docs/
│   ├── what-to-look-for.md                  ← Fields to extract from receipts/invoices
│   ├── how-to-transform.md                  ← Receipt/invoice transform format
│   ├── bank-statement-fields.md             ← Fields to extract from bank statements
│   └── how-to-transform-bank-statement.md   ← Bank statement transform format
├── workflows/                  ← The 3-stage pipeline
│   ├── CONTEXT.md              ← Pipeline routing + detection rules
│   ├── 01-extract/             ← Raw files pending parsing
│   ├── 02-load/                ← Raw extracted text (all document types)
│   └── 03-transform/
│       ├── receipts/           ← Structured receipt/invoice outputs
│       └── account-statements/ ← Structured bank statement outputs
└── parsed-files                ← Original files after successful parsing
 
```

---

## What to Load

| Task | Load These | Skip These |
|------|-----------|------------|
| Brief → Spec | The brief from `01-briefs/`, `docs/tech-standards.md` | design-system, component-library |
| Spec → Build | The spec from `02-specs/`, `docs/design-system.md`, `docs/component-library.md`, `docs/tech-standards.md` | writing-room docs |
| Review a build | The spec (as contract), the build output | docs/ (unless checking specific standards) |

---

## Skills & Tools for This Workspace

<!--
TEACHING NOTE: Production is where tools get DENSE.
Different pipeline stages use different tools. This is the
workspace-level overview — workflows/CONTEXT.md has the
stage-by-stage specifics.

Notice the pattern: skills aren't listed generically.
Each one has a WHEN (which stage) and a WHY (what it does there).
-->

| Skill / Tool | Stage | Purpose |
|-------------|-------|---------|
| `Read` (built-in) | 01-extract | Native text extraction for digital PDFs — try this first |
| `/glmocr` | 01-extract | OCR for images (jpg/jpeg/png) and scanned/image-based PDFs |

**PDF extraction order:** `Read` → if empty or garbled → `/glmocr`

**After load, detect document type** using the signal rules in `workflows/CONTEXT.md`, then route to the correct `03-transform/` subfolder.

---

## Hard Rules

1. **Do not extract additional data** Only data described in `docs/what-to-look-for.md` should be extracted, nothing less nothing more.