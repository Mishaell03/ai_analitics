import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import engine
from app.core.config import settings
from app.api.v1.router import router_v1


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as connection:
            await connection.execute(text("SELECT 1"))

        logging.info("✅ PostgreSQL connected")

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

app.include_router(router_v1)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )