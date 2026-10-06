from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict

from app.models.base import CheckDirection, CheckStatus


class CheckBase(BaseModel):
    account_id: int
    direction: CheckDirection
    check_number: str
    bank_name: str | None = None
    amount: float
    currency: str = "TRY"
    issue_date: datetime.date
    due_date: datetime.date
    status: CheckStatus = CheckStatus.PORTFOY
    endorsed_to: str | None = None
    notes: str | None = None


class CheckCreate(CheckBase):
    pass


class CheckUpdate(BaseModel):
    direction: CheckDirection | None = None
    check_number: str | None = None
    bank_name: str | None = None
    amount: float | None = None
    currency: str | None = None
    issue_date: datetime.date | None = None
    due_date: datetime.date | None = None
    status: CheckStatus | None = None
    endorsed_to: str | None = None
    notes: str | None = None


class CheckRead(CheckBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
