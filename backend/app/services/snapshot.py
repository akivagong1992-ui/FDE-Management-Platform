"""EngineerSkillSnapshot helper — 由 engineer/skill 写操作自动调用，
保持驾驶舱 Tab 7「能力成长曲线」随技能挂载实时变化。

⚠️ 设计约束（2026-05-29 用户拍板）：
- 每次技能变更要给「所有在职工程师」都 upsert 今天的快照，
  不能只给变动的那个人——否则当天数据点变成噪音（只反映一个人）
- 一天内多次变更只保留最后一次快照状态（基于 (engineer_id, snapshot_date)
  UNIQUE 约束 upsert）
"""
from datetime import date as date_cls

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.engineer import Engineer
from app.models.skill import EngineerSkill, Skill
from app.models.skill_snapshot import EngineerSkillSnapshot


LEVEL_VALUE = {"L1": 1, "L2": 2, "L3": 3}


async def take_team_snapshot(db: AsyncSession) -> None:
    """给所有 status=active 的工程师 upsert 今天的快照。

    在 attach_skill / detach_skill / create_engineer 等修改"工程师持有认证"
    的 endpoint 里，commit 数据库改动后调一次。

    实现细节：
    - skill_count = 该工程师当前 EngineerSkill 条数
    - avg_level = 所持认证的 Skill.level 平均值（L1=1, L2=2, L3=3）
    - level = 引用 engineer.level（工程师自身等级字段，与认证难度无关）
    - 同日已存在快照 → 更新字段；不存在 → 新建
    - 本函数不调 commit，由上层 endpoint 一并 commit
    """
    today = date_cls.today()

    # 1) 拉所有在职工程师
    engineers = (await db.execute(
        select(Engineer).where(Engineer.status == "active")
    )).scalars().all()
    if not engineers:
        return

    # 2) 拉所有挂载 + Skill.level，按 engineer_id 聚合
    rows = (await db.execute(
        select(EngineerSkill.engineer_id, Skill.level)
        .join(Skill, Skill.id == EngineerSkill.skill_id)
    )).all()
    counts: dict[int, int] = {}
    sums: dict[int, int] = {}
    for eid, lvl in rows:
        counts[eid] = counts.get(eid, 0) + 1
        sums[eid] = sums.get(eid, 0) + LEVEL_VALUE.get(lvl or "", 0)

    # 3) 拉今天已存在的快照，建索引
    existing_rows = (await db.execute(
        select(EngineerSkillSnapshot).where(EngineerSkillSnapshot.snapshot_date == today)
    )).scalars().all()
    existing_by_eid = {s.engineer_id: s for s in existing_rows}

    # 4) Upsert
    for e in engineers:
        cnt = counts.get(e.id, 0)
        avg = round(sums.get(e.id, 0) / cnt, 2) if cnt else 0.0
        snap = existing_by_eid.get(e.id)
        if snap is not None:
            snap.skill_count = cnt
            snap.avg_level = avg
            snap.level = e.level
        else:
            db.add(EngineerSkillSnapshot(
                engineer_id=e.id, snapshot_date=today,
                skill_count=cnt, avg_level=avg, level=e.level,
            ))

    await db.flush()
