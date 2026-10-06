from __future__ import annotations

import datetime

from pydantic import BaseModel


class IncomeExpenseSummary(BaseModel):
    period_start: datetime.date
    period_end: datetime.date
    total_income: float
    total_expense: float
    net: float
    by_category: dict[str, float] = {}


class CashflowPoint(BaseModel):
    date: datetime.date
    inflow: float
    outflow: float
    net: float
    running_balance: float


class CashflowReport(BaseModel):
    points: list[CashflowPoint]
    opening_balance: float
