from datetime import date as date_cls

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.engineer import Certificate, Engineer
from app.models.skill import EngineerSkill
from app.models.skill_snapshot import EngineerSkillSnapshot
from app.schemas.skill_snapshot import SkillSnapshotOut, SnapshotTriggerResult

router = APIRouter(prefix="/skill-snapshots", tags=["skill-snapshots"])


def _to_out(s: EngineerSkillSnapshot) -> SkillSnapshotOut:
    return SkillSnapshotOut(
        id=s.id,
        engineer_id=s.engineer_id,
        engineer_name=s.engineer.full_name if s.engineer else None,
        snapshot_date=s.snapshot_date,
        skill_count=s.skill_count,
        avg_level=s.avg_level,
        cert_count=s.cert_count,
        level=s.level,
        created_at=s.created_at,
    )


@router.get("", response_model=list[SkillSnapshotOut])
async def list_snapshots(
    engineer_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[SkillSnapshotOut]:
    stmt = select(EngineerSkillSnapshot).order_by(EngineerSkillSnapshot.snapshot_date.desc())
    if engineer_id is not None:
        stmt = stmt.where(EngineerSkillSnapshot.engineer_id == engineer_id)
    rows = (await db.execute(stmt)).scalars().all()
    return [_to_out(r) for r in rows]


@router.post("/trigger", response_model=SnapshotTriggerResult)
async def trigger_snapshot(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> SnapshotTriggerResult:
    """为所有 active 工程师拍一份当日快照。已存在同日快照则跳过。"""
    today = date_cls.today()

    # 已有今日快照的 engineer_id
    existing_today = {
        eid for (eid,) in (
            await db.execute(
                select(EngineerSkillSnapshot.engineer_id)
                .where(EngineerSkillSnapshot.snapshot_date == today)
            )
        ).all()
    }

    # 当前每工程师的 skill_count / avg_level / cert_count
    skill_agg = {
        eid: (count, float(avg))
        for (eid, count, avg) in (await db.execute(
            select(
                EngineerSkill.engineer_id,
                func.count(EngineerSkill.id),
                func.coalesce(func.avg(EngineerSkill.level), 0),
            ).group_by(EngineerSkill.engineer_id)
        )).all()
    }
    cert_agg = {
        eid: cnt
        for (eid, cnt) in (await db.execute(
            select(Certificate.engineer_id, func.count(Certificate.id))
            .group_by(Certificate.engineer_id)
        )).all()
    }

    created = 0
    skipped = 0
    engineers = (await db.execute(
        select(Engineer).where(Engineer.status == "active")
    )).scalars().all()

    for e in engineers:
        if e.id in existing_today:
            skipped += 1
            continue
        skill_count, avg_level = skill_agg.get(e.id, (0, 0.0))
        cert_count = cert_agg.get(e.id, 0)
        db.add(EngineerSkillSnapshot(
            engineer_id=e.id, snapshot_date=today,
            skill_count=skill_count, avg_level=round(avg_level, 2),
            cert_count=cert_count, level=e.level,
        ))
        created += 1

    await db.commit()
    return SnapshotTriggerResult(snapshot_date=today, created=created, skipped=skipped)


@router.get("/team-trend")
async def team_trend(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> list[dict]:
    """整团队级成长曲线：按 snapshot_date 聚合平均值。"""
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
    return [
        {
            "snapshot_date": str(d),
            "engineer_count": cnt,
            "avg_skill_count": round(float(sk), 2),
            "avg_skill_level": round(float(lvl), 2),
            "avg_cert_count": round(float(crt), 2),
        }
        for d, cnt, sk, lvl, crt in rows
    ]
