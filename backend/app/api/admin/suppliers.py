from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierOut, SupplierUpdate

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierOut])
async def list_suppliers(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[SupplierOut]:
    rows = (await db.execute(select(Supplier).order_by(Supplier.id.desc()))).scalars().all()
    return [SupplierOut.model_validate(r) for r in rows]


@router.post("", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    payload: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> SupplierOut:
    if (await db.execute(select(Supplier).where(Supplier.name == payload.name))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="供应商名称已存在")
    s = Supplier(**payload.model_dump())
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return SupplierOut.model_validate(s)


@router.patch("/{sid}", response_model=SupplierOut)
async def update_supplier(
    sid: int,
    payload: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> SupplierOut:
    s = await db.get(Supplier, sid)
    if not s:
        raise HTTPException(status_code=404, detail="供应商不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    await db.commit()
    await db.refresh(s)
    return SupplierOut.model_validate(s)


@router.delete("/{sid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    sid: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    s = await db.get(Supplier, sid)
    if not s:
        raise HTTPException(status_code=404, detail="供应商不存在")
    await db.delete(s)
    await db.commit()
