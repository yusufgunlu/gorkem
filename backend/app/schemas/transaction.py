from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict

from app.models.base import TransactionStatus, TransactionType


class TransactionBase(BaseModel):
    account_id: int
    transaction_type: TransactionType
    amount: float
    currency: str = "TRY"
    category: str | None = None
    description: str | None = None
    due_date: datetime.date
    paid_date: datetime.date | None = None
    status: TransactionStatus = TransactionStatus.BEKLIYOR


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    transaction_type: TransactionType | None = None
    amount: float | None = None
    currency: str | None = None
    category: str | None = None
    description: str | None = None
    due_date: datetime.date | None = None
    paid_date: datetime.date | None = None
    status: TransactionStatus | None = None


class TransactionRead(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_statement_line_id: int | None = None
