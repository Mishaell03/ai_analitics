from fastapi import APIRouter
from app.api.v1.routes.health import router as health_router

router_v1 = APIRouter(prefix="/api/v1")

router_v1.include_router(health_router, tags=["health"])