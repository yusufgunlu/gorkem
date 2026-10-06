from __future__ import annotations

import datetime

from sqlalchemy import Date, Enum, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import StatementFileType, StatementLineStatus, TimestampMixin


class StatementImport(Base, TimestampMixin):
    """Kullanıcının yüklediği bir banka ekstresi dosyası."""

    __tablename__ = "statement_imports"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[StatementFileType] = mapped_column(Enum(StatementFileType), nullable=False)
    bank_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    matched_rows: Mapped[int] = mapped_column(Integer, default=0)

    lines: Mapped[list["StatementLine"]] = relationship(
        back_populates="import_batch", cascade="all, delete-orphan"
    )


class StatementLine(Base, TimestampMixin):
    """Ekstre dosyasından okunan tek bir satır (hareket)."""

    __tablename__ = "statement_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("statement_imports.id"), nullable=False)

    transaction_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    raw_description: Mapped[str] = mapped_column(String(1000), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    # Pozitif: alacak (tahsilat), negatif: borç (ödeme)
    balance_after: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)

    matched_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    match_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[StatementLineStatus] = mapped_column(
        Enum(StatementLineStatus), default=StatementLineStatus.BEKLIYOR, nullable=False
    )

    import_batch: Mapped["StatementImport"] = relationship(back_populates="lines")
    matched_account: Mapped["Account | None"] = relationship()
