from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.models.project import PROJECT_KIND_REVENUE, Project
from app.models.project_revenue import REVENUE_STATUS_RECEIVED, ProjectRevenue
from app.schemas.project_revenue import (
    ProjectRevenueCreate,
    ProjectRevenueOut,
    ProjectRevenueUpdate,
)

router = APIRouter(prefix="/project-revenues", tags=["project-revenues"])


def _to_out(r: ProjectRevenue) -> ProjectRevenueOut:
    return ProjectRevenueOut(
        id=r.id,
        project_id=r.project_id,
        project_name=r.project.name if r.project else None,
        amount=r.amount,
        gross_amount=r.gross_amount,
        currency=r.currency,
        recognized_date=r.recognized_date,
        invoice_no=r.invoice_no,
        description=r.description,
        status=r.status,
        received_at=r.received_at,
        created_at=r.created_at,
    )


@router.get("", response_model=list[ProjectRevenueOut])
async def list_revenues(
    project_id: int | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> list[ProjectRevenueOut]:
    stmt = select(ProjectRevenue).order_by(ProjectRevenue.recognized_date.desc(), ProjectRevenue.id.desc())
    if project_id is not None:
        stmt = stmt.where(ProjectRevenue.project_id == project_id)
    if status_filter:
        stmt = stmt.where(ProjectRevenue.status == status_filter)
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
    r = ProjectRevenue(**payload.model_dump())
    if r.status == REVENUE_STATUS_RECEIVED and r.received_at is None:
        r.received_at = datetime.utcnow()
    db.add(r)
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
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(r, k, v)
    if data.get("status") == REVENUE_STATUS_RECEIVED and r.received_at is None:
        r.received_at = datetime.utcnow()
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
    await db.delete(r)
    await db.commit()
