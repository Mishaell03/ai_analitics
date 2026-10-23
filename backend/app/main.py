import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import engine
from app.core.config import settings
from app.core.csrf import CSRFOriginMiddleware
from app.core.minio_migration import migrate_legacy_storage
from app.api.v1.router import router_v1
from app.core.exception_handlers import register_exception_handlers
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as connection:
            await connection.execute(text("SELECT 1"))

        logging.info("✅ PostgreSQL connected")

        if settings.minio_migrate_on_startup:
            # ошибка миграции не должна мешать запуску: старые файлы
            # можно перенести позже командой `make storage-migrate`
            try:
                await migrate_legacy_storage()

            except Exception as e:
                logging.warning(f"⚠️ MinIO migration failed: {e}")

        yield

    except Exception as e:
        logging.error(f"❌ PostgreSQL connection failed: {e}")
        raise

    finally:
        await engine.dispose()
        logging.info("❌ PostgreSQL disconnected")


app = FastAPI(
    title="AI-analytics API",
    description="Users API base URL: /api",
    version="1.0.0",
    lifespan=lifespan,
)

# порядок важен: CORS должен быть снаружи CSRF, иначе браузер
# не увидит заголовки CORS у ответа 403
register_exception_handlers(app)

app.add_middleware(CSRFOriginMiddleware)

app.add_middleware(
    CORSMiddleware,
    # домены прода задаются через CORS_ORIGINS
    allow_origins=list(settings.cors_origins),
    # Allow the Vite dev server on any localhost/127.0.0.1 port so that a busy
    # port (which makes Vite pick the next one) does not break CORS/auth.
    allow_origin_regex=None if settings.is_product else r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_v1)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
