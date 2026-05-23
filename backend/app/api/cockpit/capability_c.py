"""驾驶舱 Tab 7 · 能力成长曲线（基于 EngineerSkillSnapshot）。"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.skill_snapshot import EngineerSkillSnapshot

router = APIRouter(prefix="/growth-trend", tags=["cockpit-capability"])


@router.get("")
async def growth_trend(db: AsyncSession = Depends(get_db)) -> dict:
    """整团队级成长曲线 — 按 snapshot_date 平均技能数 / 等级 / 证书。"""
    rows = (await db.execute(
        select(
            EngineerSkillSnapshot.snapshot_date,
            func.count(EngineerSkillSnapshot.id),
            func.coalesce(func.avg(EngineerSkillSnapshot.skill_count), 0),
            func.coalesce(func.avg(EngineerSkillSnapshot.avg_level), 0),
            func.coalesce(func.avg(EngineerSkillSnapshot.cert_count), 0),
        )
        .group_by(EngineerSkillSnapshot.snapshot_date)
        .order_by(EngineerSkillSnapshot.snapshot_date)
    )).all()
    series = [
        {
            "date": str(d),
            "engineer_count": int(cnt),
            "avg_skill_count": round(float(sk), 2),
            "avg_skill_level": round(float(lvl), 2),
            "avg_cert_count": round(float(crt), 2),
        }
        for d, cnt, sk, lvl, crt in rows
    ]

    # Growth deltas (latest vs earliest)
    delta_skills = (series[-1]["avg_skill_count"] - series[0]["avg_skill_count"]) if len(series) >= 2 else 0.0
    delta_level = (series[-1]["avg_skill_level"] - series[0]["avg_skill_level"]) if len(series) >= 2 else 0.0
    delta_certs = (series[-1]["avg_cert_count"] - series[0]["avg_cert_count"]) if len(series) >= 2 else 0.0

    return {
        "series": series,
        "snapshots_count": len(series),
        "growth_delta": {
            "avg_skill_count": round(delta_skills, 2),
            "avg_skill_level": round(delta_level, 2),
            "avg_cert_count": round(delta_certs, 2),
        },
    }
