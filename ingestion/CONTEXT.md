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
| **Look up what to look for in the extracted text** | `docs/what-to-look-for.md` |

**Don't read everything.** Identify your task, load only what you need.

---

## Folder Structure

```
ingestion/                      ← Parses receipts and invoices from photos, screenshots or PDFs
├── CONTEXT.md
├── docs/                       ← Voice guide, style rules, audience profiles
│   ├── how-to-transform.md
│   ├── what-to-look-for.md
├── workflows/                  ← The 3-stage pipeline
│   ├── CONTEXT.md              ← Pipeline routing
│   ├── 01-extract/             ← Files pending for successful parsing go here, all new files start here
│   ├── 02-load/                ← Parsed documents in readable md text file
│   └── 03-transform/           ← Documents with a structure previously defined go here
└── parsed-files                ← Files successfuly parsed go here, this is the by-product
 
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
| `/glmocr` | 01-extract | When extracting data from a receipt or invoice picture|

---

## Hard Rules

1. **Do not extract additional data** Only data described in `docs/what-to-look-for.md` should be extracted, nothing less nothing more.