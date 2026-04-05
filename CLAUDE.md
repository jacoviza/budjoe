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
└── ingestion/                      ← Parses receipts and invoices from photos, screenshots or PDFs
    ├── CONTEXT.md
    ├── docs/                       ← Voice guide, style rules, audience profiles
    │   ├── voice.md
    │   ├── style-guide.md
    │   └── audience.md
    ├── workflows/                  ← The 4-stage pipeline
    │   ├── CONTEXT.md              ← Pipeline routing
    │   ├── 01-extract/             ← Files pending for successful parsing go here, all new files start here
    │   ├── 02-load/                ← Parsed documents in readable md text file
    │   └── 03-transform/           ← Documents with a structure previously defined go here
    └── parsed-files                ← Files successfuly parsed go here, this is the by-product
 
```

---

## Quick Navigation

| Want to... | Go here |
|------------|---------|
| **Parse a receipt or invoice** | `ingestion/CONTEXT.md` |
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
| Parsed Receipts and Invoices | `[YYYY-MM-DD]-[commerce].md` | `2026-03-10-supermercados-nacional.md` |

---

## File Placement Rules

### Ingestion
- **Raw Receipts and invoices:** `ingestion/01-extract/[slug].[png|jpg|jpeg|pdf]`
- **Parsed receipts and documents:** `ingestion/02-load/[slug].md`
- **Structured receipts and documents:** `ingestion/03-transform/[YYYY-MM-DD-HHMMSS]-[commerce].md`
- **Parsed Receipts and invoices:** `ingestion/parsed-files/[YYYY-MM-DD]-[slug]-[status].[png|jpg|jpeg|pdf]`

---

## Token Management

<!--
TEACHING NOTE: This section is the #1 thing people miss.
It tells agents what NOT to load. Without this, agents will
try to read everything and blow their context window.
-->

**Each workspace is siloed.** Don't load everything.

- Parsing a receipt or invoice? → Load `ingestion/docs/what-to-look-for.md`.

The CONTEXT.md files tell you what to load for each task. Trust them.

---

## Auto-Ingestion Trigger

When the user attaches an image or PDF (jpg, jpeg, png, pdf) in the conversation:
1. Copy the file to `ingestion/workflows/01-extract/[original-filename]`
2. Immediately run the full pipeline without waiting for further instructions:
   - Extract → `/glmocr` on the file
   - Load → write parsed output to `ingestion/workflows/02-load/[slug].md`
   - Transform → write structured table to `ingestion/workflows/03-transform/[YYYY-MM-DD-HHMMSS]-[commerce].md`
   - Move original to `ingestion/parsed-files/[YYYY-MM-DD]-[slug]-parsed.[ext]`

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
| `/glmocr` | Skill | parsing receipts and invoices |

See each workspace's CONTEXT.md for when and how these tools get invoked.
