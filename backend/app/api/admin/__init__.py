from fastapi import APIRouter

from app.api.admin import auth, data_dict, files, users

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])
admin_router.include_router(auth.router)
admin_router.include_router(users.router)
admin_router.include_router(data_dict.router)
admin_router.include_router(files.router)
