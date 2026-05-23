from fastapi import APIRouter, Depends

from app.api.cockpit import aggregations, knowledge_c, overview, profit_c
from app.core.deps import cockpit_guard

cockpit_router = APIRouter(
    prefix="/api/cockpit",
    tags=["cockpit"],
    dependencies=[Depends(cockpit_guard)],
)
cockpit_router.include_router(overview.router)
cockpit_router.include_router(profit_c.router)
cockpit_router.include_router(knowledge_c.router)
cockpit_router.include_router(aggregations.router)
