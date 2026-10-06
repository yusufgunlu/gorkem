from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
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
    """Geliştirme ortamında tabloları doğrudan oluşturur.

    Üretimde Alembic migration'ları kullanılmalıdır.
    """
    from app import models  # noqa: F401  (modellerin Base.metadata'ya kaydı için)

    Base.metadata.create_all(bind=engine)
