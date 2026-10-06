from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Uygulama genel ayarları. Değerler .env dosyasından okunur."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "GÖRKEM"
    app_env: str = "development"
    secret_key: str = "change-this-in-production"

    database_url: str = "sqlite:///./gorkem.db"

    # Ekstre satırı <-> cari hesap eşleştirmesinde "otomatik eşleşti" kabul
    # edilecek en düşük bulanık eşleştirme skoru (0-100).
    statement_match_threshold: int = 75


@lru_cache
def get_settings() -> Settings:
    return Settings()
