from fastapi import APIRouter
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.courses import router as courses_router

router_v1 = APIRouter(prefix="/api/v1")

router_v1.include_router(health_router, tags=["Health"])
router_v1.include_router(auth_router, tags=["Auth"])
router_v1.include_router(courses_router, tags=["Courses"])