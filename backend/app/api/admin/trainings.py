from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.engineer import Engineer
from app.models.training import TrainingRecord
from app.schemas.training import TrainingCreate, TrainingOut, TrainingUpdate

router = APIRouter(prefix="/trainings", tags=["trainings"])

COST_VIEW_ROLES = {"admin", "lead", "finance"}


def _to_out(t: TrainingRecord, include_cost: bool) -> TrainingOut:
    return TrainingOut(
        id=t.id,
        engineer_id=t.engineer_id,
        engineer_name=t.engineer.full_name if t.engineer else None,
        course_name=t.course_name,
        provider=t.provider,
        category=t.category,
        training_date=t.training_date,
        hours=t.hours,
        cost=t.cost if include_cost else None,
        passed=t.passed,
        notes=t.notes,
        created_at=t.created_at,
    )


@router.get("", response_model=list[TrainingOut])
async def list_trainings(
    engineer_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> list[TrainingOut]:
    stmt = select(TrainingRecord).order_by(TrainingRecord.training_date.desc())
    if engineer_id is not None:
        stmt = stmt.where(TrainingRecord.engineer_id == engineer_id)
    rows = (await db.execute(stmt)).scalars().all()
    inc = user.get("role") in COST_VIEW_ROLES
    return [_to_out(t, inc) for t in rows]


@router.post("", response_model=TrainingOut, status_code=status.HTTP_201_CREATED)
async def create_training(
    payload: TrainingCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> TrainingOut:
    if not await db.get(Engineer, payload.engineer_id):
        raise HTTPException(status_code=400, detail="工程师不存在")
    data = payload.model_dump()
    if user.get("role") not in COST_VIEW_ROLES:
        data["cost"] = None
    t = TrainingRecord(**data)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return _to_out(t, user.get("role") in COST_VIEW_ROLES)


@router.patch("/{tid}", response_model=TrainingOut)
async def update_training(
    tid: int,
    payload: TrainingUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> TrainingOut:
    t = await db.get(TrainingRecord, tid)
    if not t:
        raise HTTPException(status_code=404, detail="培训记录不存在")
    data = payload.model_dump(exclude_unset=True)
    if "cost" in data and user.get("role") not in COST_VIEW_ROLES:
        data.pop("cost")
    for k, v in data.items():
        setattr(t, k, v)
    await db.commit()
    await db.refresh(t)
    return _to_out(t, user.get("role") in COST_VIEW_ROLES)


@router.delete("/{tid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training(
    tid: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    t = await db.get(TrainingRecord, tid)
    if not t:
        raise HTTPException(status_code=404, detail="培训记录不存在")
    await db.delete(t)
    await db.commit()
