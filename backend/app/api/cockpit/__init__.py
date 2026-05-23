from fastapi import APIRouter, Depends

from app.api.cockpit import overview
from app.core.deps import cockpit_guard

cockpit_router = APIRouter(
    prefix="/api/cockpit",
    tags=["cockpit"],
    dependencies=[Depends(cockpit_guard)],
)
cockpit_router.include_router(overview.router)
