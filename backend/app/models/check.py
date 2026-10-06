from __future__ import annotations

import datetime

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import CheckDirection, CheckStatus, TimestampMixin


class Check(Base, TimestampMixin):
    """Alınan veya verilen çek."""

    __tablename__ = "checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)

    direction: Mapped[CheckDirection] = mapped_column(Enum(CheckDirection), nullable=False)
    check_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    bank_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="TRY", nullable=False)

    issue_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    due_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    status: Mapped[CheckStatus] = mapped_column(
        Enum(CheckStatus), default=CheckStatus.PORTFOY, nullable=False
    )

    # Ciro edilmişse devredilen üçüncü taraf/banka bilgisi.
    endorsed_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    account: Mapped["Account"] = relationship(back_populates="checks")
