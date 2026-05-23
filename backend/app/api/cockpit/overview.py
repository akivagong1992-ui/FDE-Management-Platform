"""驾驶舱 Tab 1 总览 — 真实数据聚合（Phase 3-next-iii Round 4 替代 Phase 0 placeholder）。"""

from datetime import date as date_cls
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

    # 合作客户：admin 端勾选「驾驶舱展示」+ 上传 logo 即出现，不再附加项目状态条件
    # （客户能否上墙完全由 admin 决策，避免「设了为什么不显示」的困惑）
    showcase_rows = (await db.execute(
        select(NeedParty.name, NeedParty.logo_path)
        .where(NeedParty.show_in_cockpit.is_(True))
        .order_by(NeedParty.name)
    )).all()
    showcase_clients = [
        {"name": name, "logo_path": logo} for name, logo in showcase_rows
    ]

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

    # 本月完成数：actual_end_date 落在本月（驾驶舱总览以"纯计数"展示进度）
    month_start = date_cls.today().replace(day=1)
    completed_this_month = (await db.execute(
        select(func.count(Project.id)).where(
            Project.actual_end_date.is_not(None),
            Project.actual_end_date >= month_start,
        )
    )).scalar_one() or 0

    return {
        "active_projects": int(active_projects),
        "team_size": int(team_size),
        "on_time_delivery_rate": round(on_time_rate, 4),  # 保留供后端审计；前端不再展示
        "completed_this_month": int(completed_this_month),
        "showcase_clients": showcase_clients,
        "capability_by_category": capability_by_category,
        "by_status": by_status,
        "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        # 兼容旧字段（驾驶舱可能引用）
        "knowledge_assets": 0,
        "renewal_rate": 0.0,
        "certifications": 0,
    }
