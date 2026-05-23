from fastapi import APIRouter

from app.api.admin import (
    auth, data_dict, engineers, files, need_parties, projects, sales_persons, skills, users, vendors,
)

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])
admin_router.include_router(auth.router)
admin_router.include_router(users.router)
admin_router.include_router(data_dict.router)
admin_router.include_router(files.router)
admin_router.include_router(vendors.router)
admin_router.include_router(skills.router)
admin_router.include_router(engineers.router)
admin_router.include_router(need_parties.router)
admin_router.include_router(sales_persons.router)
admin_router.include_router(projects.router)
