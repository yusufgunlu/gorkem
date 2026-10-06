from __future__ import annotations

import datetime

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, TransactionStatus, TransactionType


class Transaction(Base, TimestampMixin):
    """Gelir veya gider hareketi, bir cari hesapla ilişkilidir."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)

    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="TRY", nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    due_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    paid_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)

    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus), default=TransactionStatus.BEKLIYOR, nullable=False
    )

    # Bu hareket bir ekstre satırından otomatik oluşturulduysa kaynağı.
    source_statement_line_id: Mapped[int | None] = mapped_column(
        ForeignKey("statement_lines.id"), nullable=True
    )

    account: Mapped["Account"] = relationship(back_populates="transactions")
