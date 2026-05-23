"""驾驶舱 Tab 1 总览 — 真实数据聚合（Phase 3-next-iii Round 4 替代 Phase 0 placeholder）。"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.engineer import Engineer
from app.models.need_party import NeedParty
from app.models.project import (
    PROJECT_STATUS_ARCHIVED,
    PROJECT_STATUS_CLOSING,
    PROJECT_STATUS_DRAFTING,
    Project,
)
from app.models.skill import EngineerSkill, Skill

router = APIRouter(prefix="/overview", tags=["cockpit-overview"])


@router.get("")
async def overview_kpi(db: AsyncSession = Depends(get_db)) -> dict:
    # 在管项目：除归档外
    active_projects = (await db.execute(
        select(func.count(Project.id)).where(Project.status != PROJECT_STATUS_ARCHIVED)
    )).scalar_one() or 0

    # 团队规模：active 工程师
    team_size = (await db.execute(
        select(func.count(Engineer.id)).where(Engineer.status == "active")
    )).scalar_one() or 0

    # 按时交付率：已验收/收尾/归档 + 有 actual_end 的 / 其中按时的
    finished_q = (
        select(Project).where(
            Project.status.in_([PROJECT_STATUS_CLOSING, PROJECT_STATUS_ARCHIVED]),
            Project.planned_end_date.is_not(None),
            Project.actual_end_date.is_not(None),
        )
    )
    finished_projects = (await db.execute(finished_q)).scalars().all()
    on_time_count = sum(
        1 for p in finished_projects if p.actual_end_date <= p.planned_end_date
    )
    on_time_rate = (on_time_count / len(finished_projects)) if finished_projects else 0.0

    # 已交付客户：拥有 closing/archived 项目的不同需求方
    delivered_clients_rows = (await db.execute(
        select(distinct(NeedParty.name))
        .join(Project, Project.need_party_id == NeedParty.id)
        .where(Project.status.in_([PROJECT_STATUS_CLOSING, PROJECT_STATUS_ARCHIVED]))
        .order_by(NeedParty.name)
    )).scalars().all()

    # 能力矩阵：每个 skill_category 下不同工程师数
    cap_rows = (await db.execute(
        select(Skill.category, func.count(distinct(EngineerSkill.engineer_id)))
        .join(EngineerSkill, EngineerSkill.skill_id == Skill.id)
        .group_by(Skill.category)
    )).all()
    capability_by_category = sorted(
        [{"category": cat, "engineer_count": int(cnt)} for cat, cnt in cap_rows],
        key=lambda x: -x["engineer_count"],
    )

    # 项目状态分布（驾驶舱小卡片可能用到）
    by_status_rows = (await db.execute(
        select(Project.status, func.count(Project.id)).group_by(Project.status)
    )).all()
    by_status = [{"label": s, "count": int(c)} for s, c in by_status_rows]

    return {
        "active_projects": int(active_projects),
        "team_size": int(team_size),
        "on_time_delivery_rate": round(on_time_rate, 4),
        "delivered_clients": list(delivered_clients_rows),
        "capability_by_category": capability_by_category,
        "by_status": by_status,
        "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        # 兼容旧字段（驾驶舱可能引用）
        "knowledge_assets": 0,
        "renewal_rate": 0.0,
        "certifications": 0,
    }
