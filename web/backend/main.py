"""
Finance Control Panel - FastAPI backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import accounts, transactions, notifications, actions

app = FastAPI(
    title="Finance Control Panel",
    description="Web UI for personal finances workspace",
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite + dev servers
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(actions.router, prefix="/api/actions", tags=["actions"])


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
