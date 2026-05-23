from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.engineer import Engineer
from app.models.idp import IDP
from app.schemas.idp import IDPCreate, IDPOut, IDPUpdate

router = APIRouter(prefix="/idps", tags=["idps"])


def _to_out(i: IDP) -> IDPOut:
    return IDPOut(
        id=i.id,
        engineer_id=i.engineer_id,
        engineer_name=i.engineer.full_name if i.engineer else None,
        title=i.title,
        target_skills=i.target_skills,
        target_certs=i.target_certs,
        plan_actions=i.plan_actions,
        due_date=i.due_date,
        status=i.status,
        mentor_user_id=i.mentor_user_id,
        created_at=i.created_at,
        updated_at=i.updated_at,
    )


@router.get("", response_model=list[IDPOut])
async def list_idps(
    engineer_id: int | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[IDPOut]:
    stmt = select(IDP).order_by(IDP.id.desc())
    if engineer_id is not None:
        stmt = stmt.where(IDP.engineer_id == engineer_id)
    if status_filter:
        stmt = stmt.where(IDP.status == status_filter)
    rows = (await db.execute(stmt)).scalars().all()
    return [_to_out(r) for r in rows]


@router.post("", response_model=IDPOut, status_code=status.HTTP_201_CREATED)
async def create_idp(
    payload: IDPCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> IDPOut:
    if not await db.get(Engineer, payload.engineer_id):
        raise HTTPException(status_code=400, detail="工程师不存在")
    i = IDP(**payload.model_dump())
    db.add(i)
    await db.commit()
    await db.refresh(i)
    return _to_out(i)


@router.patch("/{idp_id}", response_model=IDPOut)
async def update_idp(
    idp_id: int,
    payload: IDPUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> IDPOut:
    i = await db.get(IDP, idp_id)
    if not i:
        raise HTTPException(status_code=404, detail="IDP 不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(i, k, v)
    await db.commit()
    await db.refresh(i)
    return _to_out(i)


@router.delete("/{idp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_idp(
    idp_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    i = await db.get(IDP, idp_id)
    if not i:
        raise HTTPException(status_code=404, detail="IDP 不存在")
    await db.delete(i)
    await db.commit()
