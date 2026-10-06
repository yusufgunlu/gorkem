from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict

from app.models.base import StatementFileType, StatementLineStatus


class StatementLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_date: datetime.date
    raw_description: str
    amount: float
    balance_after: float | None = None
    matched_account_id: int | None = None
    matched_account_name: str | None = None
    match_confidence: float | None = None
    status: StatementLineStatus


class StatementImportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_type: StatementFileType
    bank_name: str | None = None
    total_rows: int
    matched_rows: int
    lines: list[StatementLineRead] = []


class StatementLineConfirm(BaseModel):
    """Bir ekstre satırının eşleşmesini onaylama/düzeltme isteği."""

    account_id: int
    create_transaction: bool = True


class StatementLineReject(BaseModel):
    reason: str | None = None
