from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.data_dict import DataDict
from app.schemas.data_dict import DataDictCreate, DataDictOut, DataDictUpdate

router = APIRouter(prefix="/data-dict", tags=["data-dict"])


@router.get("", response_model=list[DataDictOut])
async def list_dict(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[DataDictOut]:
    stmt = select(DataDict).order_by(DataDict.category, DataDict.sort_order, DataDict.id)
    if category:
        stmt = stmt.where(DataDict.category == category)
    result = await db.execute(stmt)
    return [DataDictOut.model_validate(d) for d in result.scalars().all()]


@router.post("", response_model=DataDictOut, status_code=status.HTTP_201_CREATED)
async def create_dict(
    payload: DataDictCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> DataDictOut:
    item = DataDict(**payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return DataDictOut.model_validate(item)


@router.patch("/{item_id}", response_model=DataDictOut)
async def update_dict(
    item_id: int,
    payload: DataDictUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> DataDictOut:
    item = await db.get(DataDict, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="字典项不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    await db.commit()
    await db.refresh(item)
    return DataDictOut.model_validate(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dict(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    item = await db.get(DataDict, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="字典项不存在")
    await db.delete(item)
    await db.commit()
