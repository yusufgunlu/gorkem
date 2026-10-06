from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()
database_url = settings.resolved_database_url()

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Tüm ORM modellerinin türeyeceği taban sınıf."""


def get_db() -> Generator:
    """FastAPI dependency: istek bazlı veritabanı oturumu sağlar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Eksik tabloları oluşturur (var olanlara dokunmaz).

    Masaüstü uygulaması kendi SQLite dosyasını yönettiğinden her açılışta
    çağrılması güvenlidir. Şema değişiklikleri için Alembic migration'ları
    (bkz. `alembic/`) de kullanılabilir.
    """
    from app import models  # noqa: F401  (modellerin Base.metadata'ya kaydı için)

    Base.metadata.create_all(bind=engine)
