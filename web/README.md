# Finance Control Panel

A web-based control panel for managing personal finances - built with React + Vite (frontend) and FastAPI (backend).

## Quick Start

### Backend (Terminal 1)

```bash
cd web/backend
python -m uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`

### Frontend (Terminal 2)

```bash
cd web/frontend
npm run dev
```

The app will open at `http://localhost:5173`

## Architecture

- **Backend**: FastAPI with SQLite database (reuses existing `db/lib.py`)
- **Frontend**: React + TypeScript + Vite with React Router for navigation

## Features

### Pages

- **Accounts** (`/accounts`) - Grid view of all accounts with latest balances
- **Account Detail** (`/accounts/:id`) - Account info, statements, and transaction table
  - Edit individual transactions
  - Move transactions between accounts
- **Notifications** (`/notifications`) - Review and approve/reject bank notification transactions
  - Bulk approve/reject with checkboxes
- **Actions** (`/actions`) - Run workspace commands and view pending files
  - Database migrations
  - Load notifications
  - List pending transforms

### API Endpoints

All endpoints are under `/api/`:

**Accounts**
- `GET /accounts` - List all accounts
- `GET /accounts/{id}` - Get account with statements
- `GET /accounts/{id}/transactions` - Get account transactions (paginated)

**Transactions**
- `GET /transactions/{id}` - Get transaction
- `PATCH /transactions/{id}` - Edit transaction
- `POST /transactions/{id}/move` - Move to different account

**Notifications**
- `GET /notifications/pending` - Get pending notifications
- `PATCH /notifications/{id}/status` - Update status
- `POST /notifications/bulk-status` - Bulk update

**Actions**
- `POST /actions/migrate` - Run DB migrations
- `GET /actions/migrate/status` - Get migration status
- `POST /actions/load-notifications` - Load pending notifications
- `GET /actions/pending-files` - List unprocessed files

## Development

### Dependencies

Already installed, but if needed:

```bash
# Backend
cd web/backend
python -m pip install --user -r requirements.txt

# Frontend
cd web/frontend
npm install
```

### Building for Production

```bash
cd web/frontend
npm run build
# Output goes to web/frontend/dist/
```

## File Structure

```
web/
├── backend/
│   ├── main.py          - FastAPI app
│   ├── db.py            - DB connection wrapper
│   ├── models.py        - Pydantic models
│   ├── routers/
│   │   ├── accounts.py
│   │   ├── transactions.py
│   │   ├── notifications.py
│   │   └── actions.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── api/client.ts    - API client functions
    │   ├── types/index.ts   - TypeScript interfaces
    │   ├── pages/           - Page components
    │   └── components/      - UI components
    └── vite.config.ts
```
