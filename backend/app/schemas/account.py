from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.models.base import AccountType


class AccountBase(BaseModel):
    name: str
    account_type: AccountType = AccountType.MUSTERI
    tax_number: str | None = None
    iban: str | None = None
    phone: str | None = None
    email: str | None = None
    match_aliases: str | None = None
    opening_balance: float = 0
    notes: str | None = None


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: str | None = None
    account_type: AccountType | None = None
    tax_number: str | None = None
    iban: str | None = None
    phone: str | None = None
    email: str | None = None
    match_aliases: str | None = None
    opening_balance: float | None = None
    notes: str | None = None


class AccountRead(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    current_balance: float = 0
