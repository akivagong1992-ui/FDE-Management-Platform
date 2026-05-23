"""管理后台利润 API — 仅 lead/finance/admin 可见（口径 A + B）。

⚠️ 这些数字**绝不能**出现在 /api/cockpit/* 任何响应里（合规：公司不允许 Vendor 留剩余利润）。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.services.profit import (
    compute_by_need_party,
    compute_by_sales_person,
    compute_overall,
    compute_per_project,
)

router = APIRouter(prefix="/profit", tags=["profit-admin"])


@router.get("/overall")
async def overall(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> dict:
    """口径 A · 团队整体利润（必为正数；用于内部对账）。"""
    return await compute_overall(db)


@router.get("/per-project")
async def per_project(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> list[dict]:
    """口径 B 底表：每个 revenue 项目的 收入/成本/毛利（可正可负）。"""
    return await compute_per_project(db)


@router.get("/by-sales-person")
async def by_sales_person(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> list[dict]:
    """口径 B · 按销售人员汇总（红 / 绿区分盈亏，催回款/判断合作）。"""
    return await compute_by_sales_person(db)


@router.get("/by-need-party")
async def by_need_party(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> list[dict]:
    """口径 B · 按客户（需求方）汇总。"""
    return await compute_by_need_party(db)
