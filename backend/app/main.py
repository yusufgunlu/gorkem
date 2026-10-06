from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.paths import get_app_dir
from app.web.routes import router as web_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Masaüstü uygulamasında ayrı bir ops/DBA adımı olmadığı için eksik
    # tablolar her açılışta otomatik oluşturulur (var olanlara dokunulmaz).
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(get_app_dir() / "static")), name="static")

app.include_router(api_router)
app.include_router(web_router)


@app.get("/health")
def health() -> dict:
    """Masaüstü başlatıcısının (desktop_app.py) sunucunun hazır olduğunu
    anlamak için yokladığı hafif uç nokta."""
    return {"status": "ok"}
