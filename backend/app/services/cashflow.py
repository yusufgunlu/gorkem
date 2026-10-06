"""Gelir/gider hareketleri ve çekleri birleştirip nakit akışı projeksiyonu üretir."""

from __future__ import annotations

import datetime
from collections import defaultdict

from app.models.base import CheckDirection, CheckStatus, TransactionType
from app.models.check import Check
from app.models.transaction import Transaction
from app.schemas.report import CashflowPoint, CashflowReport

# Nakit akışını etkilemeyen çek durumları (henüz tahsil/ödenmemiş, ciro
# edilmiş veya iade/karşılıksız olanlar kendi vade tarihinde değerlendirilir;
# bu basit modelde tüm aktif çekler vade tarihinde nakde etki eder).
_INACTIVE_CHECK_STATUSES = {CheckStatus.KARSILIKSIZ, CheckStatus.IADE}


def build_cashflow_report(
    transactions: list[Transaction],
    checks: list[Check],
    opening_balance: float,
    start: datetime.date,
    end: datetime.date,
) -> CashflowReport:
    """`start`-`end` aralığında günlük giriş/çıkış ve kümülatif bakiye üretir."""

    daily: dict[datetime.date, dict[str, float]] = defaultdict(
        lambda: {"inflow": 0.0, "outflow": 0.0}
    )

    for tx in transactions:
        if not (start <= tx.due_date <= end):
            continue
        amount = float(tx.amount)
        if tx.transaction_type == TransactionType.GELIR:
            daily[tx.due_date]["inflow"] += amount
        else:
            daily[tx.due_date]["outflow"] += amount

    for check in checks:
        if check.status in _INACTIVE_CHECK_STATUSES:
            continue
        if not (start <= check.due_date <= end):
            continue
        amount = float(check.amount)
        if check.direction == CheckDirection.ALINAN:
            daily[check.due_date]["inflow"] += amount
        else:
            daily[check.due_date]["outflow"] += amount

    points: list[CashflowPoint] = []
    running_balance = opening_balance
    current = start
    while current <= end:
        day = daily.get(current, {"inflow": 0.0, "outflow": 0.0})
        net = day["inflow"] - day["outflow"]
        running_balance += net
        points.append(
            CashflowPoint(
                date=current,
                inflow=day["inflow"],
                outflow=day["outflow"],
                net=net,
                running_balance=running_balance,
            )
        )
        current += datetime.timedelta(days=1)

    return CashflowReport(points=points, opening_balance=opening_balance)


def summarize_income_expense(
    transactions: list[Transaction], start: datetime.date, end: datetime.date
) -> tuple[float, float, dict[str, float]]:
    """Toplam gelir, toplam gider ve kategori bazlı kırılım döner."""
    total_income = 0.0
    total_expense = 0.0
    by_category: dict[str, float] = defaultdict(float)

    for tx in transactions:
        if not (start <= tx.due_date <= end):
            continue
        amount = float(tx.amount)
        category = tx.category or "Diğer"
        if tx.transaction_type == TransactionType.GELIR:
            total_income += amount
            by_category[f"gelir:{category}"] += amount
        else:
            total_expense += amount
            by_category[f"gider:{category}"] += amount

    return total_income, total_expense, dict(by_category)
