from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.need_party import NeedParty
from app.schemas.need_party import NeedPartyCreate, NeedPartyOut, NeedPartyUpdate

router = APIRouter(prefix="/need-parties", tags=["need-parties"])


@router.get("", response_model=list[NeedPartyOut])
async def list_parties(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[NeedPartyOut]:
    rows = (await db.execute(select(NeedParty).order_by(NeedParty.id.desc()))).scalars().all()
    return [NeedPartyOut.model_validate(r) for r in rows]


@router.post("", response_model=NeedPartyOut, status_code=status.HTTP_201_CREATED)
async def create_party(
    payload: NeedPartyCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> NeedPartyOut:
    if (await db.execute(select(NeedParty).where(NeedParty.name == payload.name))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="需求方名称已存在")
    obj = NeedParty(**payload.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return NeedPartyOut.model_validate(obj)


@router.patch("/{party_id}", response_model=NeedPartyOut)
async def update_party(
    party_id: int,
    payload: NeedPartyUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> NeedPartyOut:
    obj = await db.get(NeedParty, party_id)
    if not obj:
        raise HTTPException(status_code=404, detail="需求方不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return NeedPartyOut.model_validate(obj)


@router.delete("/{party_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_party(
    party_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    obj = await db.get(NeedParty, party_id)
    if not obj:
        raise HTTPException(status_code=404, detail="需求方不存在")
    await db.delete(obj)
    await db.commit()
