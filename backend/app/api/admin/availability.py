"""工程师档期可用性视图

业务定义：某天工程师"忙" = 当天被任何 approval_status≠rejected 且 status≠cancelled 的派单覆盖。
日期取 actual_start_date / actual_end_date，没填则回退 planned_*。end 为空视为开口区间（仍占用）。
"""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.assignment import (
    APPROVAL_REJECTED,
    ASSIGNMENT_STATUS_CANCELLED,
    Assignment,
)
from app.models.engineer import STATUS_ACTIVE, Engineer
from app.models.project import Project
from app.models.vendor import Vendor


router = APIRouter(prefix="/availability", tags=["availability"])

PM_ROLES = {"admin", "lead", "pm", "finance"}


def _coerce_date_range(a: Assignment) -> tuple[date | None, date | None]:
    s = a.actual_start_date or a.planned_start_date
    e = a.actual_end_date or a.planned_end_date
    return s, e


@router.get("/engineers")
async def engineer_availability(
    weeks: int = Query(4, ge=1, le=12),
    from_date: date | None = Query(None, alias="from"),
    vendor_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    role = user.get("role")
    today = date.today()
    start = from_date or today
    end = start + timedelta(days=weeks * 7 - 1)

    # 工程师范围（按 role scoping）
    eng_stmt = select(Engineer).where(Engineer.status == STATUS_ACTIVE)
    if role == "engineer":
        eid = user.get("engineer_id")
        if not eid:
            return {"from": start.isoformat(), "to": end.isoformat(), "engineers": []}
        eng_stmt = eng_stmt.where(Engineer.id == eid)
    elif role == "vendor":
        vid = user.get("vendor_id")
        if not vid:
            raise HTTPException(status_code=403, detail="vendor 账号未挂公司")
        eng_stmt = eng_stmt.where(Engineer.vendor_id == vid)
    elif role not in PM_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if vendor_id is not None and role in PM_ROLES:
        eng_stmt = eng_stmt.where(Engineer.vendor_id == vendor_id)
    eng_stmt = eng_stmt.order_by(Engineer.vendor_id, Engineer.full_name)
    engineers = (await db.execute(eng_stmt)).scalars().all()
    if not engineers:
        return {"from": start.isoformat(), "to": end.isoformat(), "engineers": []}
    eng_ids = [e.id for e in engineers]

    # 拉时间窗内所有未 rejected / 未 cancelled 的派单
    asn_stmt = (
        select(Assignment, Project.name)
        .join(Project, Assignment.project_id == Project.id)
        .where(
            Assignment.engineer_id.in_(eng_ids),
            Assignment.approval_status != APPROVAL_REJECTED,
            Assignment.status != ASSIGNMENT_STATUS_CANCELLED,
        )
    )
    asn_rows = (await db.execute(asn_stmt)).all()

    # 按 engineer 聚合：每个工程师 -> [(start, end, asn_id, project_name)]
    spans_by_eng: dict[int, list[tuple[date, date, int, str]]] = {eid: [] for eid in eng_ids}
    for a, project_name in asn_rows:
        s, e = _coerce_date_range(a)
        if s is None:
            continue
        # end 为空 => 开口；裁到窗口右端
        s_eff = max(s, start)
        e_eff = min(e, end) if e else end
        if s_eff > e_eff:
            continue
        spans_by_eng[a.engineer_id].append((s_eff, e_eff, a.id, project_name))

    # 为每个 engineer 构造每日数据
    vendor_cache: dict[int, str] = {
        v.id: v.name for v in (await db.execute(select(Vendor))).scalars().all()
    }

    days_count = (end - start).days + 1
    result_engineers = []
    for e in engineers:
        spans = spans_by_eng.get(e.id, [])
        days = []
        for i in range(days_count):
            d = start + timedelta(days=i)
            covering = [(aid, pname) for (s, ee, aid, pname) in spans if s <= d <= ee]
            days.append({
                "date": d.isoformat(),
                "busy": len(covering) > 0,
                "assignments": [{"id": aid, "project_name": pname} for aid, pname in covering],
            })
        # 这段时间总忙碌天数（便于 PM 排序"找最闲的"）
        busy_days = sum(1 for d in days if d["busy"])
        result_engineers.append({
            "id": e.id,
            "full_name": e.full_name,
            "vendor_id": e.vendor_id,
            "vendor_name": vendor_cache.get(e.vendor_id),
            "days": days,
            "busy_day_count": busy_days,
            "free_day_count": days_count - busy_days,
        })

    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "weeks": weeks,
        "engineers": result_engineers,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
