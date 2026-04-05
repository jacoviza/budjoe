# Acme DevRel — Task Router

<!--
=======================================================================
TEACHING NOTE: This is LAYER 2 — THE ROUTER.

This file does ONE job: route agents to the right workspace.
It should be SHORT. 30-50 lines of actual content.

Rules for this file:
  - No detailed instructions (workspace CONTEXT.md handles that)
  - No file placement rules (CLAUDE.md handles that)
  - Just: "What's your task? → Go here. You'll also need X."

The "You'll Also Need" column is critical. It tells agents what
CROSS-WORKSPACE resources to pull. Without it, an agent building
a community post won't know to load the writing-room voice guide.
=======================================================================
-->

## What This Is

My personal finances workspace. One workspace, handling receipts and invoices ELT.

**CLAUDE.md** (always loaded) has the full folder map and naming rules. This file routes you to work.

---

## Task Routing

| Your Task | Go Here | You'll Also Need |
|-----------|---------|-----------------|
| **Parse a receipt or invoice** | `ingestion/CONTEXT.md | `docs/what-to-look-for.md` |

---

## Workspace Summary

| Workspace | Purpose | Skills & Tools |
|-----------|---------|---------------|
| `ingestion/` | Pictures and screenshots → Structured md files with receipts and invoices. | `/glmocr` |

Each workspace has its own CONTEXT.md with full details. Read that when working in a workspace, not this file.

---

## Cross-Workspace Flow

There is only one workspace at the moment

<!--
TEACHING NOTE: This diagram appears in both CLAUDE.md and CONTEXT.md.
That's intentional — CLAUDE.md shows it as part of the permanent map,
CONTEXT.md shows it as part of routing context. The duplication is
small (4 lines) and serves different readers (the always-loaded map
vs. the task-specific router).
-->
