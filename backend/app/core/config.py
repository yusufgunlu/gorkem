from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.paths import get_data_dir


class Settings(BaseSettings):
    """Uygulama genel ayarları. Değerler .env dosyasından okunur."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "GÖRKEM"
    app_env: str = "development"
    secret_key: str = "change-this-in-production"

    # Boş bırakılırsa (varsayılan), masaüstü uygulaması için kullanıcının
    # veri dizinindeki (örn. Windows'ta %APPDATA%\GORKEM) bir SQLite
    # dosyası kullanılır. DATABASE_URL ortam değişkeni ile (örn. prod'da
    # PostgreSQL) geçersiz kılınabilir.
    database_url: str = ""

    # Ekstre satırı <-> cari hesap eşleştirmesinde "otomatik eşleşti" kabul
    # edilecek en düşük bulanık eşleştirme skoru (0-100).
    statement_match_threshold: int = 75

    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        db_path = get_data_dir() / "gorkem.db"
        return f"sqlite:///{db_path.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
