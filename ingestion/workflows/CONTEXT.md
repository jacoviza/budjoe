# Workflows — The Production Pipeline


## What This Folder Is

Two stages, each in its own folder. An agent enters one stage, does its work, and outputs to the next.

```
01-extract/  →  02-load/      →   03-transform/
  (extract)       (load)            (transform)
```

---

## Agent Routing

| Your Task | Input | Also Load | Output | Skills at This Stage |
|-----------|-------|-----------|--------|---------------------|
| Extract → Load | File from `01-ingest/` | `../docs/what-to-look-for.md` | Parsed md document in `02-load/`. Original file is moved to `../parsed-files/` | /glmocr |
| Load → Transform | Markdown file from `02-load/` | `../docs/how-to-transform.md` | Final deliverable in `03-transform/` | - |

---

## Stage Details

### 01-extract/ — The Input

Pictures and screenshots of receipts and invoices that are intended to be parsed.

**File pattern:** `[slug].jpg`, `[slug].jpeg`, `[slug].png`, `[slug].pdf`

**Skills activate here:**
- `/glmocr` - to extract data from receipts and invoices



### 02-load/ — The first transformation

A md file containing all the receipt's or invoice's details.

**File pattern:** `[slug].md`

---

**What a parsed document includes:**
- Date and time of the transaction
- Name of the merchant
- Sub-total of the bill (before taxes)
- Total of the bill
- Taxes (ITBIS, IVA, etc)
- What "done" looks like

**What a spec does NOT include:**
- Promotional codes
- Personal information


**File pattern:** `[YYYY-MM-DD-HH:MM:SS]-[commerce].md`


**Skills activate here:**
- `/glmocr` — parse receipts and invoices. Uses OCR to extract text from images.


### 03-transform/ — The Work

Where the core details of receipts and invoices are distiled into an md file. The parser reads the load md files then creates a new md file with the core details of the desired output.

**File pattern:** `[YYYY-MM-DD-HH:MM:SS]-[commerce]-parsed.md/` 

---

## Pipeline Rules

1. **Flow is forward.** extract → load → transform. No skipping stages.
2. **Each agent loads only what it needs.** See the routing table above.
3. **The parser does not have creative freedom.** It must return only the expected data.

---

## Where Skills Wire Into the Pipeline (Summary)

```
01-extract/          02-load/           03-transform/ 
                    ┌─────────────┐                     
                    │ /glmocr     │
                    │             │                     
                    └─────────────┘ 
```
