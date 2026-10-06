from fastapi import APIRouter

from app.api.v1 import accounts, checks, reports, statements, transactions

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(accounts.router)
api_router.include_router(transactions.router)
api_router.include_router(checks.router)
api_router.include_router(statements.router)
api_router.include_router(reports.router)
