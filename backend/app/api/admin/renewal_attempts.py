from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.project import Project
from app.models.renewal_attempt import (
    RENEWAL_OUTCOME_LOST,
    RENEWAL_OUTCOME_WON,
    RenewalAttempt,
)
from app.models.user import User
from app.schemas.renewal_attempt import (
    RenewalAttemptCreate,
    RenewalAttemptOut,
    RenewalAttemptUpdate,
)

router = APIRouter(prefix="/renewal-attempts", tags=["renewal-attempts"])


async def _user_id_from_jwt(db: AsyncSession, user: dict) -> int | None:
    username = user.get("sub")
    if not username:
        return None
    u = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    return u.id if u else None


def _to_out(r: RenewalAttempt) -> RenewalAttemptOut:
    return RenewalAttemptOut(
        id=r.id,
        previous_project_id=r.previous_project_id,
        previous_project_name=r.previous_project.name if r.previous_project else None,
        attempt_date=r.attempt_date,
        outcome=r.outcome,
        won_project_id=r.won_project_id,
        won_project_name=r.won_project.name if r.won_project else None,
        lost_reason=r.lost_reason,
        lost_reason_note=r.lost_reason_note,
        notes=r.notes,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.get("", response_model=list[RenewalAttemptOut])
async def list_attempts(
    outcome: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[RenewalAttemptOut]:
    stmt = select(RenewalAttempt).order_by(RenewalAttempt.attempt_date.desc(), RenewalAttempt.id.desc())
    if outcome:
        stmt = stmt.where(RenewalAttempt.outcome == outcome)
    rows = (await db.execute(stmt)).scalars().all()
    return [_to_out(r) for r in rows]


def _validate_outcome_fields(outcome: str, won_pid: int | None, lost_reason: str | None) -> None:
    if outcome == RENEWAL_OUTCOME_WON and won_pid is None:
        raise HTTPException(status_code=400, detail="outcome=won 必须指定 won_project_id")
    if outcome == RENEWAL_OUTCOME_LOST and not lost_reason:
        raise HTTPException(status_code=400, detail="outcome=lost 必须填 lost_reason")


@router.post("", response_model=RenewalAttemptOut, status_code=status.HTTP_201_CREATED)
async def create_attempt(
    payload: RenewalAttemptCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead", "pm")),
) -> RenewalAttemptOut:
    if not await db.get(Project, payload.previous_project_id):
        raise HTTPException(status_code=400, detail="previous_project 不存在")
    if payload.won_project_id and not await db.get(Project, payload.won_project_id):
        raise HTTPException(status_code=400, detail="won_project 不存在")
    _validate_outcome_fields(payload.outcome, payload.won_project_id, payload.lost_reason)

    r = RenewalAttempt(**payload.model_dump())
    r.created_by_user_id = await _user_id_from_jwt(db, user)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return _to_out(r)


@router.patch("/{rid}", response_model=RenewalAttemptOut)
async def update_attempt(
    rid: int,
    payload: RenewalAttemptUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> RenewalAttemptOut:
    r = await db.get(RenewalAttempt, rid)
    if not r:
        raise HTTPException(status_code=404, detail="续单记录不存在")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(r, k, v)
    _validate_outcome_fields(r.outcome, r.won_project_id, r.lost_reason)
    await db.commit()
    await db.refresh(r)
    return _to_out(r)


@router.delete("/{rid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attempt(
    rid: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    r = await db.get(RenewalAttempt, rid)
    if not r:
        raise HTTPException(status_code=404, detail="续单记录不存在")
    await db.delete(r)
    await db.commit()
