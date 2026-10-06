from __future__ import annotations

from sqlalchemy import Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AccountType, TimestampMixin


class Account(Base, TimestampMixin):
    """Cari hesap: müşteri veya tedarikçi."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType), default=AccountType.MUSTERI, nullable=False
    )
    tax_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    iban: Mapped[str | None] = mapped_column(String(34), index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Ekstre eşleştirmesinde kullanılacak ek anahtar kelimeler (virgülle
    # ayrılmış), örn. "ACME LTD, ACME LOJISTIK, ACME TIC"
    match_aliases: Mapped[str | None] = mapped_column(String(500), nullable=True)

    opening_balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    checks: Mapped[list["Check"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )

    def alias_list(self) -> list[str]:
        if not self.match_aliases:
            return [self.name]
        return [self.name] + [a.strip() for a in self.match_aliases.split(",") if a.strip()]
