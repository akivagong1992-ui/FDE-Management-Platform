"""驾驶舱口径 C 接口 — 节省金额 + 无收入项目创造价值。
驾驶舱口径 D（限定版）— 公司毛利率提升仅暴露 3 个百分率，藏掉所有绝对金额。

⚠️ 绝不返回口径 A/B 的数字（团队真实毛利、销售/客户层面应收应付）。
⚠️ D 限定版刻意不暴露 gross / team_revenue / non_service_expense / outsource_benchmark / extra_profit
   等绝对金额，避免侧信道反推团队真实利润。详见 docs/VARIABLES.md §2.4 + PLAN.md §0 A4。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.profit import (
    compute_cockpit_savings_and_value,
    compute_company_margin_lift,
)

router = APIRouter(tags=["cockpit-profit-c"])


@router.get("/savings-and-value")
async def savings_and_value(db: AsyncSession = Depends(get_db)) -> dict:
    return await compute_cockpit_savings_and_value(db)


@router.get("/margin-lift-pct")
async def margin_lift_pct(db: AsyncSession = Depends(get_db)) -> dict:
    """D 口径 · 公司毛利率提升 — 仅 3 个百分率 + 项目数。"""
    full = await compute_company_margin_lift(db)
    return {
        "outsource_margin_pct": round(full["outsource_margin_pct"], 2),
        "fde_margin_pct": round(full["fde_margin_pct"], 2),
        "margin_lift_pct": round(full["margin_lift_pct"], 2),
        "counted_projects": full["counted_projects"],
        "unit": "%",
    }
