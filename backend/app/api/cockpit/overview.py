from fastapi import APIRouter

router = APIRouter(prefix="/overview", tags=["cockpit-overview"])


@router.get("")
async def overview_kpi() -> dict:
    """Phase 0 placeholder — returns mock KPIs for cockpit big-screen."""
    return {
        "active_projects": 14,
        "cumulative_margin_hkd": 12_840_000,
        "team_size": 87,
        "outsource_saving_hkd": 3_560_000,
        "on_time_delivery_rate": 0.92,
        "knowledge_assets": 156,
        "renewal_rate": 0.78,
        "certifications": 42,
        "updated_at": "2026-05-23T10:00:00+08:00",
        "_phase": "phase-0-placeholder",
    }
