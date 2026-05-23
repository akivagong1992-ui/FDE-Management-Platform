from fastapi import APIRouter

from app.api.admin import (
    assignments, auth, data_dict, engineers, expenses, files, knowledge_assets, need_parties,
    profit, project_revenues, projects, retrospectives, sales_persons, skills, suppliers,
    timesheets, users, vendor_service_fees, vendors,
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
admin_router.include_router(assignments.router)
admin_router.include_router(timesheets.router)
admin_router.include_router(suppliers.router)
admin_router.include_router(expenses.router)
admin_router.include_router(vendor_service_fees.router)
admin_router.include_router(project_revenues.router)
admin_router.include_router(profit.router)
admin_router.include_router(knowledge_assets.router)
admin_router.include_router(retrospectives.router)
