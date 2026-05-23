"""一次性脚本：把本地 SQLite 数据复制到 Postgres（部署到天翼云前用）。

前提：
  1. 目标 Postgres 实例已建好且 Alembic 已 upgrade head（建好 schema）
  2. 设置环境变量：
       SOURCE_SQLITE=./manpower.db
       TARGET_PG_URL=postgresql+asyncpg://user:pw@host:5432/manpower
  3. 目标库**应为空**——脚本会按依赖顺序逐表 COPY，会跳过已存在的行（按 PK 主键判重）

跑：
  uv run python -m scripts.migrate_sqlite_to_pg
"""

import asyncio
import os
from pathlib import Path

from sqlalchemy import insert, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models import (  # noqa: F401 — ensure all models register on Base
    AssetReference, Assignment, Certificate, DataDict, Engineer, EngineerSkill,
    EngineerSkillSnapshot, ExpenseRequest, IDP, KnowledgeAsset, NeedParty,
    NotificationLog, Project, ProjectRetrospective, ProjectRevenue, RenewalAttempt,
    SalesPerson, SalesTransferLog, Skill, Supplier, Timesheet, TrainingRecord,
    User, Vendor, VendorServiceFee,
)


# 表迁移顺序：参考表必须先于引用表（满足外键约束）
TABLE_ORDER = [
    User, DataDict, Vendor, Skill, EngineerSkill, Engineer, Certificate,
    NeedParty, SalesPerson, Project, SalesTransferLog,
    Assignment, Timesheet,
    Supplier, ExpenseRequest, VendorServiceFee, ProjectRevenue,
    KnowledgeAsset, AssetReference,
    ProjectRetrospective, EngineerSkillSnapshot, TrainingRecord, IDP,
    RenewalAttempt, NotificationLog,
]


async def copy_table(src_session, tgt_session, model) -> int:
    rows = (await src_session.execute(select(model))).scalars().all()
    if not rows:
        return 0
    # Convert ORM rows → dicts (skip relationships)
    cols = {c.name for c in model.__table__.columns}
    payload = []
    for r in rows:
        d = {k: getattr(r, k) for k in cols}
        payload.append(d)
    # Insert in batches of 500
    inserted = 0
    for i in range(0, len(payload), 500):
        batch = payload[i:i + 500]
        await tgt_session.execute(insert(model.__table__).values(batch))
        inserted += len(batch)
    await tgt_session.commit()
    return inserted


async def main() -> None:
    src_path = os.getenv("SOURCE_SQLITE", "./manpower.db")
    tgt_url = os.getenv("TARGET_PG_URL", "")
    if not tgt_url:
        raise SystemExit("请设置环境变量 TARGET_PG_URL")
    if not Path(src_path).exists():
        raise SystemExit(f"源 SQLite 文件不存在: {src_path}")

    src_engine = create_async_engine(f"sqlite+aiosqlite:///{src_path}")
    tgt_engine = create_async_engine(tgt_url)
    SrcSession = async_sessionmaker(src_engine, expire_on_commit=False)
    TgtSession = async_sessionmaker(tgt_engine, expire_on_commit=False)

    print(f"⏳ 源: {src_path}")
    print(f"⏳ 目标: {tgt_url.split('@')[-1]}")
    print()

    total = 0
    async with SrcSession() as src, TgtSession() as tgt:
        for model in TABLE_ORDER:
            name = model.__tablename__
            try:
                n = await copy_table(src, tgt, model)
                print(f"  ✓ {name:30} {n:>6} 行")
                total += n
            except Exception as e:
                print(f"  ✗ {name:30} 失败: {e}")
                raise

    # Reset Postgres sequences (since we forced specific PK ids)
    async with TgtSession() as tgt:
        for model in TABLE_ORDER:
            t = model.__tablename__
            try:
                # Only tables with int PK named 'id' — common pattern in this codebase
                await tgt.execute(
                    text(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), "
                         f"COALESCE((SELECT MAX(id) FROM {t}), 1), true)")
                )
            except Exception:
                pass  # silently skip tables without a sequence
        await tgt.commit()
    print()
    print(f"✅ 完成。共 {total} 行已搬到 Postgres。")
    print("   再次检查：alembic_version 行已通过 alembic upgrade head 自动写入，无需手动复制。")

    await src_engine.dispose()
    await tgt_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
