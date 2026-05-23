"""驾驶舱 Tab 6 · 技术沉淀统计 — 仅成果数字（数量/分布），不含金额。"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.data_dict import DataDict
from app.models.knowledge_asset import KnowledgeAsset

router = APIRouter(prefix="/knowledge-stats", tags=["cockpit-knowledge"])


@router.get("")
async def knowledge_stats(db: AsyncSession = Depends(get_db)) -> dict:
    total = (await db.execute(select(func.count(KnowledgeAsset.id)))).scalar_one() or 0

    # By category
    by_cat_rows = (await db.execute(
        select(KnowledgeAsset.category, func.count(KnowledgeAsset.id))
        .group_by(KnowledgeAsset.category)
    )).all()
    cat_labels = {
        r.code: r.label for r in (
            await db.execute(select(DataDict).where(DataDict.category == "asset_category"))
        ).scalars().all()
    }
    by_category = [
        {"code": code, "label": cat_labels.get(code, code), "count": cnt}
        for code, cnt in by_cat_rows
    ]
    by_category.sort(key=lambda x: -x["count"])

    # Recent 30 days
    cutoff = datetime.utcnow() - timedelta(days=30)
    recent = (await db.execute(
        select(func.count(KnowledgeAsset.id)).where(KnowledgeAsset.created_at >= cutoff)
    )).scalar_one() or 0

    # Projects that produced at least one asset
    proj_cov = (await db.execute(
        select(func.count(distinct(KnowledgeAsset.project_id)))
        .where(KnowledgeAsset.project_id.is_not(None))
    )).scalar_one() or 0

    return {
        "total_assets": int(total),
        "by_category": by_category,
        "recent_30d": int(recent),
        "project_coverage": int(proj_cov),
        # No money fields by design — keeps cockpit isolation invariant
    }
