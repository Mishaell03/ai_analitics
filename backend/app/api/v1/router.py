from fastapi import APIRouter
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.courses import router as courses_router
from app.api.v1.routes.exercises import router as exercises_router
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.admin import router as admin_router

router_v1 = APIRouter(prefix="/api/v1")

router_v1.include_router(health_router, tags=["Health"])
router_v1.include_router(auth_router, tags=["Auth"])
router_v1.include_router(courses_router, tags=["Courses"])
router_v1.include_router(users_router, tags=["Users"])
router_v1.include_router(admin_router, tags=["Admin"])
router_v1.include_router(exercises_router, tags=["Exercises"])
