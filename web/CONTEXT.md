# Web — Finance Control Panel

## What This Is

A local web UI for managing personal finances. FastAPI backend on port **8000**, React/Vite frontend on port **5173**. Both read from `db/finance.db` (the shared SQLite database).

---

## How to Start

```bash
# Terminal 1 — Backend
cd web/backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd web/frontend
npm run dev
```

Open `http://localhost:5173` in the browser.

---

## Architecture at a Glance

```
web/
├── backend/
│   ├── main.py          ← FastAPI app, CORS config, router wiring
│   ├── db.py            ← DB connection (wraps db/lib.py)
│   ├── models.py        ← Pydantic request/response models
│   └── routers/
│       ├── accounts.py        GET /api/accounts, GET /api/accounts/{id}
│       ├── transactions.py    GET/PATCH /api/transactions/{id}, POST …/move
│       ├── notifications.py   GET/PATCH /api/notifications/…, POST …/bulk-status
│       ├── actions.py         POST /api/actions/migrate, POST …/load-notifications
│       └── duplicates.py      GET/POST /api/duplicates/…
└── frontend/
    └── src/
        ├── api/           API client — all fetch calls live here
        ├── types/         TypeScript interfaces that mirror backend models
        ├── context/       React context providers (e.g. theme)
        ├── components/    Reusable UI pieces (layout, transaction table, etc.)
        └── pages/         One file per route
            ├── AccountsPage.tsx
            ├── AccountDetailPage.tsx
            ├── NotificationsPage.tsx
            ├── DuplicatesPage.tsx
            └── ActionsPage.tsx
```

---

## Pages

| Route | File | Purpose |
|-------|------|---------|
| `/accounts` | `AccountsPage.tsx` | Grid of all accounts with balances |
| `/accounts/:id` | `AccountDetailPage.tsx` | Statements + inline-editable transaction table |
| `/notifications` | `NotificationsPage.tsx` | Review & bulk approve/reject pending notifications |
| `/duplicates` | `DuplicatesPage.tsx` | Detect and resolve duplicate transactions |
| `/actions` | `ActionsPage.tsx` | Run DB migrations, load notifications, view pending files |

---

## What to Load When

- **Adding a new page or route** → Read `web/frontend/src/App.tsx` for routing, pick the nearest page as a model.
- **Adding a new API endpoint** → Read the matching `web/backend/routers/<name>.py`. Add new router files to `main.py`.
- **Changing DB queries** → Read `web/backend/db.py` and the router; never bypass `db/lib.py`.
- **Styling** → Each page has a `*.module.css` co-located file. Dark mode tokens are in `DARK_MODE_GUIDE.md`.
- **TypeScript types** → `web/frontend/src/types/index.ts` — keep in sync with backend Pydantic models.

---

## Key Constraints

- The backend is **read-write** to `db/finance.db` — all mutations go through the API, never direct DB writes from the frontend.
- CORS is locked to `localhost:5173` and `localhost:3000` in `main.py`. Adjust there if you change the frontend port.
- Do not add new Python dependencies without updating `requirements.txt`.
- Do not add new npm packages without confirming pnpm is the package manager (`pnpm-lock.yaml` is the lock file).
