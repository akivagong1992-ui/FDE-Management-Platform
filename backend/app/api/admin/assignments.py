from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.assignment import (
    ASSIGNMENT_STATUS_ENDED,
    Assignment,
)
from app.models.engineer import Engineer
from app.models.project import Project
from app.schemas.assignment import AssignmentCreate, AssignmentOut, AssignmentUpdate

router = APIRouter(prefix="/assignments", tags=["assignments"])


def _to_out(a: Assignment) -> AssignmentOut:
    return AssignmentOut(
        id=a.id,
        engineer_id=a.engineer_id,
        engineer_name=a.engineer.full_name if a.engineer else None,
        project_id=a.project_id,
        project_name=a.project.name if a.project else None,
        project_code=a.project.code if a.project else None,
        role=a.role,
        allocation_ratio=a.allocation_ratio,
        planned_start_date=a.planned_start_date,
        planned_end_date=a.planned_end_date,
        actual_start_date=a.actual_start_date,
        actual_end_date=a.actual_end_date,
        status=a.status,
        notes=a.notes,
        created_at=a.created_at,
    )


@router.get("", response_model=list[AssignmentOut])
async def list_assignments(
    engineer_id: int | None = None,
    project_id: int | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[AssignmentOut]:
    stmt = select(Assignment).order_by(Assignment.id.desc())
    if engineer_id is not None:
        stmt = stmt.where(Assignment.engineer_id == engineer_id)
    if project_id is not None:
        stmt = stmt.where(Assignment.project_id == project_id)
    if status_filter:
        stmt = stmt.where(Assignment.status == status_filter)
    rows = (await db.execute(stmt)).scalars().all()
    return [_to_out(a) for a in rows]


@router.post("", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    payload: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> AssignmentOut:
    eng = await db.get(Engineer, payload.engineer_id)
    if not eng:
        raise HTTPException(status_code=400, detail="工程师不存在")
    proj = await db.get(Project, payload.project_id)
    if not proj:
        raise HTTPException(status_code=400, detail="项目不存在")
    a = Assignment(**payload.model_dump())
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return _to_out(a)


@router.patch("/{assignment_id}", response_model=AssignmentOut)
async def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> AssignmentOut:
    a = await db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="派单不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    await db.commit()
    await db.refresh(a)
    return _to_out(a)


@router.post("/{assignment_id}/end", response_model=AssignmentOut)
async def end_assignment(
    assignment_id: int,
    actual_end_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm")),
) -> AssignmentOut:
    from datetime import date as date_cls

    a = await db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="派单不存在")
    a.status = ASSIGNMENT_STATUS_ENDED
    if actual_end_date:
        a.actual_end_date = date_cls.fromisoformat(actual_end_date)
    elif a.actual_end_date is None:
        a.actual_end_date = date_cls.today()
    await db.commit()
    await db.refresh(a)
    return _to_out(a)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    a = await db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="派单不存在")
    await db.delete(a)
    await db.commit()
