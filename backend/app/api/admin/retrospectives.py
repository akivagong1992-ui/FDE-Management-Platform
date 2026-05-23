from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.project import Project
from app.models.retrospective import ProjectRetrospective
from app.models.user import User
from app.schemas.retrospective import (
    RetrospectiveCreate,
    RetrospectiveOut,
    RetrospectiveUpdate,
)

router = APIRouter(prefix="/retrospectives", tags=["retrospectives"])


async def _user_id_from_jwt(db: AsyncSession, user: dict) -> int | None:
    username = user.get("sub")
    if not username:
        return None
    u = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    return u.id if u else None


def _to_out(r: ProjectRetrospective) -> RetrospectiveOut:
    return RetrospectiveOut(
        id=r.id,
        project_id=r.project_id,
        project_name=r.project.name if r.project else None,
        satisfaction_score=r.satisfaction_score,
        what_went_well=r.what_went_well,
        what_to_improve=r.what_to_improve,
        action_items=r.action_items,
        next_review_date=r.next_review_date,
        is_closed=r.is_closed,
        created_by_user_id=r.created_by_user_id,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.get("", response_model=list[RetrospectiveOut])
async def list_retros(
    project_id: int | None = None,
    is_closed: bool | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[RetrospectiveOut]:
    stmt = select(ProjectRetrospective).order_by(ProjectRetrospective.id.desc())
    if project_id is not None:
        stmt = stmt.where(ProjectRetrospective.project_id == project_id)
    if is_closed is not None:
        stmt = stmt.where(ProjectRetrospective.is_closed == is_closed)
    rows = (await db.execute(stmt)).scalars().all()
    return [_to_out(r) for r in rows]


@router.post("", response_model=RetrospectiveOut, status_code=status.HTTP_201_CREATED)
async def create_retro(
    payload: RetrospectiveCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> RetrospectiveOut:
    if not await db.get(Project, payload.project_id):
        raise HTTPException(status_code=400, detail="项目不存在")
    r = ProjectRetrospective(**payload.model_dump())
    r.created_by_user_id = await _user_id_from_jwt(db, user)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return _to_out(r)


@router.patch("/{rid}", response_model=RetrospectiveOut)
async def update_retro(
    rid: int,
    payload: RetrospectiveUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> RetrospectiveOut:
    r = await db.get(ProjectRetrospective, rid)
    if not r:
        raise HTTPException(status_code=404, detail="复盘记录不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(r, k, v)
    await db.commit()
    await db.refresh(r)
    return _to_out(r)


@router.delete("/{rid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_retro(
    rid: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    r = await db.get(ProjectRetrospective, rid)
    if not r:
        raise HTTPException(status_code=404, detail="复盘记录不存在")
    await db.delete(r)
    await db.commit()
