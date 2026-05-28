from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorOut, VendorUpdate

router = APIRouter(prefix="/vendors", tags=["vendors"])


@router.get("", response_model=list[VendorOut])
async def list_vendors(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[VendorOut]:
    result = await db.execute(select(Vendor).order_by(Vendor.id.desc()))
    return [VendorOut.model_validate(v) for v in result.scalars().all()]


@router.post("", response_model=VendorOut, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    payload: VendorCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> VendorOut:
    if (await db.execute(select(Vendor).where(Vendor.name == payload.name))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Vendor 名称已存在")
    v = Vendor(**payload.model_dump())
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return VendorOut.model_validate(v)


@router.patch("/{vendor_id}", response_model=VendorOut)
async def update_vendor(
    vendor_id: int,
    payload: VendorUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> VendorOut:
    v = await db.get(Vendor, vendor_id)
    if not v:
        raise HTTPException(status_code=404, detail="Vendor 不存在")
    for k, val in payload.model_dump(exclude_unset=True).items():
        setattr(v, k, val)
    await db.commit()
    await db.refresh(v)
    return VendorOut.model_validate(v)


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(
    vendor_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    v = await db.get(Vendor, vendor_id)
    if not v:
        raise HTTPException(status_code=404, detail="Vendor 不存在")
    await db.delete(v)
    await db.commit()
