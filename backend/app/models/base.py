import datetime
import enum

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )


class AccountType(str, enum.Enum):
    MUSTERI = "musteri"
    TEDARIKCI = "tedarikci"
    DIGER = "diger"


class TransactionType(str, enum.Enum):
    GELIR = "gelir"
    GIDER = "gider"


class TransactionStatus(str, enum.Enum):
    BEKLIYOR = "bekliyor"
    ODENDI = "odendi"
    GECIKTI = "gecikti"


class CheckDirection(str, enum.Enum):
    ALINAN = "alinan"
    VERILEN = "verilen"


class CheckStatus(str, enum.Enum):
    PORTFOY = "portfoy"
    CIRO = "ciro"
    TAHSIL = "tahsil"
    KARSILIKSIZ = "karsiliksiz"
    IADE = "iade"


class StatementFileType(str, enum.Enum):
    EXCEL = "excel"
    PDF = "pdf"


class StatementLineStatus(str, enum.Enum):
    ESLESTI = "eslesti"
    BEKLIYOR = "bekliyor"
    MANUEL = "manuel"
    REDDEDILDI = "reddedildi"
