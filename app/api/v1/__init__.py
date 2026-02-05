from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1.operators import router as operators_router
from app.api.v1.calls import router as calls_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.settings import router as settings_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(tenants_router, prefix="/tenants", tags=["Tenants"])
router.include_router(operators_router, prefix="/operators", tags=["Operators"])
router.include_router(calls_router, prefix="/calls", tags=["Calls"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(settings_router, prefix="/settings", tags=["Settings"])
