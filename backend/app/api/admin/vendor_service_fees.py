from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.engineer import Engineer
from app.models.project import Project
from app.models.vendor import Vendor
from app.models.vendor_service_fee import VSF_STATUS_PAID, VendorServiceFee
from app.schemas.vendor_service_fee import (
    VendorServiceFeeCreate,
    VendorServiceFeeOut,
    VendorServiceFeeUpdate,
)

router = APIRouter(prefix="/vendor-service-fees", tags=["vendor-service-fees"])


def _to_out(v: VendorServiceFee) -> VendorServiceFeeOut:
    return VendorServiceFeeOut(
        id=v.id,
        vendor_id=v.vendor_id,
        vendor_name=v.vendor.name if v.vendor else None,
        engineer_id=v.engineer_id,
        engineer_name=v.engineer.full_name if v.engineer else None,
        project_id=v.project_id,
        project_name=v.project.name if v.project else None,
        fee_type=v.fee_type,
        period_start=v.period_start,
        period_end=v.period_end,
        amount=v.amount,
        currency=v.currency,
        invoice_no=v.invoice_no,
        description=v.description,
        status=v.status,
        paid_at=v.paid_at,
        created_at=v.created_at,
    )


@router.get("", response_model=list[VendorServiceFeeOut])
async def list_fees(
    vendor_id: int | None = None,
    engineer_id: int | None = None,
    project_id: int | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> list[VendorServiceFeeOut]:
    stmt = select(VendorServiceFee).order_by(VendorServiceFee.period_start.desc(), VendorServiceFee.id.desc())
    if vendor_id is not None:
        stmt = stmt.where(VendorServiceFee.vendor_id == vendor_id)
    if engineer_id is not None:
        stmt = stmt.where(VendorServiceFee.engineer_id == engineer_id)
    if project_id is not None:
        stmt = stmt.where(VendorServiceFee.project_id == project_id)
    if status_filter:
        stmt = stmt.where(VendorServiceFee.status == status_filter)
    rows = (await db.execute(stmt)).scalars().all()
    return [_to_out(v) for v in rows]


@router.post("", response_model=VendorServiceFeeOut, status_code=status.HTTP_201_CREATED)
async def create_fee(
    payload: VendorServiceFeeCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> VendorServiceFeeOut:
    if not await db.get(Vendor, payload.vendor_id):
        raise HTTPException(status_code=400, detail="Vendor 不存在")
    if payload.engineer_id is not None and not await db.get(Engineer, payload.engineer_id):
        raise HTTPException(status_code=400, detail="工程师不存在")
    if payload.project_id is not None and not await db.get(Project, payload.project_id):
        raise HTTPException(status_code=400, detail="项目不存在")
    if payload.period_end < payload.period_start:
        raise HTTPException(status_code=400, detail="period_end 不能早于 period_start")

    v = VendorServiceFee(**payload.model_dump())
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return _to_out(v)


@router.patch("/{fid}", response_model=VendorServiceFeeOut)
async def update_fee(
    fid: int,
    payload: VendorServiceFeeUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> VendorServiceFeeOut:
    v = await db.get(VendorServiceFee, fid)
    if not v:
        raise HTTPException(status_code=404, detail="服务费记录不存在")
    data = payload.model_dump(exclude_unset=True)
    for k, val in data.items():
        setattr(v, k, val)
    if data.get("status") == VSF_STATUS_PAID and v.paid_at is None:
        v.paid_at = datetime.utcnow()
    await db.commit()
    await db.refresh(v)
    return _to_out(v)


@router.delete("/{fid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fee(
    fid: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    v = await db.get(VendorServiceFee, fid)
    if not v:
        raise HTTPException(status_code=404, detail="服务费记录不存在")
    await db.delete(v)
    await db.commit()
