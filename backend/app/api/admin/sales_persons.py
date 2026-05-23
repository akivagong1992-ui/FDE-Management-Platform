from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.sales_person import SalesPerson
from app.schemas.sales_person import SalesPersonCreate, SalesPersonOut, SalesPersonUpdate

router = APIRouter(prefix="/sales-persons", tags=["sales-persons"])


@router.get("", response_model=list[SalesPersonOut])
async def list_sales(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[SalesPersonOut]:
    stmt = select(SalesPerson).order_by(SalesPerson.id.desc())
    if active_only:
        stmt = stmt.where(SalesPerson.is_active.is_(True))
    rows = (await db.execute(stmt)).scalars().all()
    return [SalesPersonOut.model_validate(r) for r in rows]


@router.post("", response_model=SalesPersonOut, status_code=status.HTTP_201_CREATED)
async def create_sales(
    payload: SalesPersonCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> SalesPersonOut:
    if (await db.execute(select(SalesPerson).where(SalesPerson.name == payload.name))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="销售人员姓名已存在")
    obj = SalesPerson(**payload.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return SalesPersonOut.model_validate(obj)


@router.patch("/{sales_id}", response_model=SalesPersonOut)
async def update_sales(
    sales_id: int,
    payload: SalesPersonUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> SalesPersonOut:
    obj = await db.get(SalesPerson, sales_id)
    if not obj:
        raise HTTPException(status_code=404, detail="销售人员不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return SalesPersonOut.model_validate(obj)


@router.delete("/{sales_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sales(
    sales_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    obj = await db.get(SalesPerson, sales_id)
    if not obj:
        raise HTTPException(status_code=404, detail="销售人员不存在")
    # Soft delete via is_active 更稳妥; 这里允许真删（若被引用，FK 阻止）
    await db.delete(obj)
    await db.commit()
