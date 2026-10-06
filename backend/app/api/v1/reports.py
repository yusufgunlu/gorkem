import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.account import Account
from app.models.check import Check
from app.models.transaction import Transaction
from app.schemas.report import CashflowReport, IncomeExpenseSummary
from app.services.cashflow import build_cashflow_report, summarize_income_expense

router = APIRouter(prefix="/reports", tags=["Raporlar"])


@router.get("/income-expense", response_model=IncomeExpenseSummary)
def income_expense_report(
    start: datetime.date = Query(..., description="Dönem başlangıcı"),
    end: datetime.date = Query(..., description="Dönem sonu"),
    db: Session = Depends(get_db),
) -> IncomeExpenseSummary:
    transactions = list(db.scalars(select(Transaction)).all())
    total_income, total_expense, by_category = summarize_income_expense(transactions, start, end)
    return IncomeExpenseSummary(
        period_start=start,
        period_end=end,
        total_income=total_income,
        total_expense=total_expense,
        net=total_income - total_expense,
        by_category=by_category,
    )


@router.get("/cashflow", response_model=CashflowReport)
def cashflow_report(
    start: datetime.date = Query(..., description="Dönem başlangıcı"),
    end: datetime.date = Query(..., description="Dönem sonu"),
    db: Session = Depends(get_db),
) -> CashflowReport:
    transactions = list(db.scalars(select(Transaction)).all())
    checks = list(db.scalars(select(Check)).all())
    opening_balance = sum(float(a.opening_balance) for a in db.scalars(select(Account)).all())
    return build_cashflow_report(transactions, checks, opening_balance, start, end)
