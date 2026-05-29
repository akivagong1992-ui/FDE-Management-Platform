"""项目收入登记。

⛔ pass-through 不变量（2026-05-28 Akiva 锁定）：
    每笔 ProjectRevenue 都同步一笔等额 VSF 镜像（同 project + 同 vendor + 同 amount）。
    create/update/delete 必须维护这个不变量。
    见 tests/test_revenue_vsf_sync.py 锁定测试。
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.models.project import PROJECT_KIND_REVENUE, Project
from app.models.project_revenue import ProjectRevenue
from app.models.vendor import Vendor
from app.models.vendor_service_fee import (
    VSF_STATUS_DRAFT,
    VSF_TYPE_PROJECT_MILESTONE,
    VendorServiceFee,
)
from app.schemas.project_revenue import (
    ProjectRevenueCreate,
    ProjectRevenueOut,
    ProjectRevenueUpdate,
)

router = APIRouter(prefix="/project-revenues", tags=["project-revenues"])

MIRROR_DESC = "自动镜像自 ProjectRevenue (pass-through)"


def _to_out(r: ProjectRevenue) -> ProjectRevenueOut:
    return ProjectRevenueOut(
        id=r.id,
        project_id=r.project_id,
        project_name=r.project.name if r.project else None,
        vendor_id=r.vendor_id,
        vendor_name=r.vendor.name if r.vendor else None,
        amount=r.amount,
        gross_amount=r.gross_amount,
        non_service_expense=r.non_service_expense,
        currency=r.currency,
        recognized_date=r.recognized_date,
        invoice_no=r.invoice_no,
        description=r.description,
        created_at=r.created_at,
    )


async def _find_mirror_vsf(db: AsyncSession, r: ProjectRevenue) -> VendorServiceFee | None:
    """找跟某条 ProjectRevenue 一对一镜像的 VSF（按 project + vendor + recognized_date + 自动镜像标记）。
    现阶段一个 (project, vendor, date) 组合应只有一条镜像 VSF。
    """
    stmt = select(VendorServiceFee).where(
        VendorServiceFee.project_id == r.project_id,
        VendorServiceFee.vendor_id == r.vendor_id,
        VendorServiceFee.period_start == r.recognized_date,
        VendorServiceFee.description == MIRROR_DESC,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def _create_mirror_vsf(db: AsyncSession, r: ProjectRevenue) -> None:
    """根据 ProjectRevenue 同步建一笔 VSF 镜像。"""
    vsf = VendorServiceFee(
        vendor_id=r.vendor_id,
        project_id=r.project_id,
        fee_type=VSF_TYPE_PROJECT_MILESTONE,
        period_start=r.recognized_date,
        period_end=r.recognized_date,
        amount=r.amount,
        currency=r.currency,
        status=VSF_STATUS_DRAFT,
        description=MIRROR_DESC,
    )
    db.add(vsf)


@router.get("", response_model=list[ProjectRevenueOut])
async def list_revenues(
    project_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> list[ProjectRevenueOut]:
    stmt = select(ProjectRevenue).order_by(ProjectRevenue.recognized_date.desc(), ProjectRevenue.id.desc())
    if project_id is not None:
        stmt = stmt.where(ProjectRevenue.project_id == project_id)
    rows = (await db.execute(stmt)).scalars().all()
    return [_to_out(r) for r in rows]


@router.post("", response_model=ProjectRevenueOut, status_code=status.HTTP_201_CREATED)
async def create_revenue(
    payload: ProjectRevenueCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> ProjectRevenueOut:
    p = await db.get(Project, payload.project_id)
    if not p:
        raise HTTPException(status_code=400, detail="项目不存在")
    if p.kind != PROJECT_KIND_REVENUE:
        raise HTTPException(
            status_code=400,
            detail="只能给「有收入」类型的项目登记收入；如要修改，请先把项目类型改回 revenue",
        )
    v = await db.get(Vendor, payload.vendor_id)
    if not v:
        raise HTTPException(status_code=400, detail="经办 vendor 不存在")
    r = ProjectRevenue(**payload.model_dump())
    db.add(r)
    await db.flush()  # 拿到 r.id 后再建镜像 VSF
    await _create_mirror_vsf(db, r)
    await db.commit()
    await db.refresh(r)
    return _to_out(r)


@router.patch("/{rid}", response_model=ProjectRevenueOut)
async def update_revenue(
    rid: int,
    payload: ProjectRevenueUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> ProjectRevenueOut:
    r = await db.get(ProjectRevenue, rid)
    if not r:
        raise HTTPException(status_code=404, detail="收入记录不存在")

    # 改 vendor / amount / recognized_date 都要同步 VSF 镜像
    data = payload.model_dump(exclude_unset=True)
    if "vendor_id" in data:
        v = await db.get(Vendor, data["vendor_id"])
        if not v:
            raise HTTPException(status_code=400, detail="经办 vendor 不存在")

    # 先找老镜像（基于改之前的字段）
    old_mirror = await _find_mirror_vsf(db, r)

    for k, val in data.items():
        setattr(r, k, val)
    await db.flush()

    # 同步镜像 VSF：删旧建新（简单可靠，避免 vendor/date/amount 多个字段分支判断）
    if old_mirror is not None:
        await db.delete(old_mirror)
        await db.flush()
    await _create_mirror_vsf(db, r)

    await db.commit()
    await db.refresh(r)
    return _to_out(r)


@router.delete("/{rid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_revenue(
    rid: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    r = await db.get(ProjectRevenue, rid)
    if not r:
        raise HTTPException(status_code=404, detail="收入记录不存在")
    # 先删镜像 VSF
    mirror = await _find_mirror_vsf(db, r)
    if mirror is not None:
        await db.delete(mirror)
    await db.delete(r)
    await db.commit()
