"""驾驶舱口径 C 接口 — 节省金额 + 无收入项目创造价值。

⚠️ 绝不返回口径 A/B 的数字（团队真实毛利、销售/客户层面应收应付）。
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.profit import compute_cockpit_savings_and_value

router = APIRouter(prefix="/savings-and-value", tags=["cockpit-profit-c"])


@router.get("")
async def savings_and_value(db: AsyncSession = Depends(get_db)) -> dict:
    return await compute_cockpit_savings_and_value(db)
