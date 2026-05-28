from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.assignment import (
    APPROVAL_ACCEPTED,
    APPROVAL_PENDING,
    APPROVAL_REJECTED,
    ASSIGNMENT_STATUS_ENDED,
    MSG_FROM_ENGINEER,
    MSG_FROM_PM,
    MSG_FROM_SYSTEM,
    Assignment,
    AssignmentMessage,
)
from app.models.engineer import Engineer
from app.models.project import Project
from app.models.user import User
from app.schemas.assignment import (
    AssignmentAccept,
    AssignmentCreate,
    AssignmentMessageOut,
    AssignmentOut,
    AssignmentReject,
    AssignmentReply,
    AssignmentUpdate,
)

router = APIRouter(prefix="/assignments", tags=["assignments"])

# 管理者角色（能创建、编辑、看全部派单）
PM_ROLES = {"admin", "lead", "pm"}
ENGINEER_ROLE = "engineer"


def _to_out(a: Assignment, message_count: int | None = None) -> AssignmentOut:
    return AssignmentOut(
        id=a.id,
        engineer_id=a.engineer_id,
        engineer_name=a.engineer.full_name if a.engineer else None,
        project_id=a.project_id,
        project_name=a.project.name if a.project else None,
        project_code=a.project.code if a.project else None,
        role=a.role,
        planned_start_date=a.planned_start_date,
        planned_end_date=a.planned_end_date,
        actual_start_date=a.actual_start_date,
        actual_end_date=a.actual_end_date,
        status=a.status,
        approval_status=a.approval_status,
        engineer_responded_at=a.engineer_responded_at,
        created_by_user_id=a.created_by_user_id,
        notes=a.notes,
        message_count=message_count if message_count is not None else len(a.messages or []),
        created_at=a.created_at,
    )


def _msg_to_out(m: AssignmentMessage, sender_name: str | None) -> AssignmentMessageOut:
    return AssignmentMessageOut(
        id=m.id,
        sender_user_id=m.sender_user_id,
        sender_name=sender_name,
        sender_kind=m.sender_kind,
        body=m.body,
        created_at=m.created_at,
    )


async def _user_name_lookup(db: AsyncSession, user_ids: list[int]) -> dict[int, str]:
    if not user_ids:
        return {}
    rows = (await db.execute(
        select(User.id, User.full_name, User.username).where(User.id.in_(user_ids))
    )).all()
    return {uid: (fn or un) for uid, fn, un in rows}


async def _assert_can_access_assignment(a: Assignment, user: dict) -> None:
    """非 PM 角色（engineer）只能访问 engineer_id 匹配自己的派单。"""
    if user.get("role") in PM_ROLES:
        return
    if user.get("role") == ENGINEER_ROLE and a.engineer_id == user.get("engineer_id"):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该派单")


# ─── List / detail ─────────────────────────────────────────────────────

@router.get("", response_model=list[AssignmentOut])
async def list_assignments(
    engineer_id: int | None = None,
    project_id: int | None = None,
    status_filter: str | None = None,
    approval_filter: str | None = None,
    mine_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> list[AssignmentOut]:
    stmt = select(Assignment).order_by(Assignment.id.desc())

    # engineer 角色强制只看自己；mine_only 由 PM 用于「我创建的」筛选（暂未启用）
    if user.get("role") == ENGINEER_ROLE:
        eng_id = user.get("engineer_id")
        if not eng_id:
            return []
        stmt = stmt.where(Assignment.engineer_id == eng_id)
    elif user.get("role") not in PM_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if engineer_id is not None:
        stmt = stmt.where(Assignment.engineer_id == engineer_id)
    if project_id is not None:
        stmt = stmt.where(Assignment.project_id == project_id)
    if status_filter:
        stmt = stmt.where(Assignment.status == status_filter)
    if approval_filter:
        stmt = stmt.where(Assignment.approval_status == approval_filter)

    rows = (await db.execute(stmt)).scalars().all()
    return [_to_out(a) for a in rows]


@router.get("/{assignment_id}/messages", response_model=list[AssignmentMessageOut])
async def list_messages(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> list[AssignmentMessageOut]:
    a = await db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="派单不存在")
    await _assert_can_access_assignment(a, user)
    msgs = a.messages or []
    name_map = await _user_name_lookup(db, [m.sender_user_id for m in msgs if m.sender_user_id])
    return [_msg_to_out(m, name_map.get(m.sender_user_id or 0)) for m in msgs]


# ─── Create / update / delete (PM only) ────────────────────────────────

@router.post("", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    payload: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead")),
) -> AssignmentOut:
    eng = await db.get(Engineer, payload.engineer_id)
    if not eng:
        raise HTTPException(status_code=400, detail="工程师不存在")
    proj = await db.get(Project, payload.project_id)
    if not proj:
        raise HTTPException(status_code=400, detail="项目不存在")

    data = payload.model_dump(exclude={"initial_message"})
    a = Assignment(
        **data,
        approval_status=APPROVAL_PENDING,
        created_by_user_id=user.get("user_id"),
    )
    db.add(a)
    await db.flush()

    # 系统消息：告诉工程师派单到了
    pm_name = user.get("sub", "管理员")
    sys_msg = AssignmentMessage(
        assignment_id=a.id, sender_user_id=user.get("user_id"),
        sender_kind=MSG_FROM_SYSTEM,
        body=f"{pm_name} 向你派单：{proj.name} · 角色 {payload.role or '未指定'}。请确认接单或拒单。",
    )
    db.add(sys_msg)
    if payload.initial_message:
        db.add(AssignmentMessage(
            assignment_id=a.id, sender_user_id=user.get("user_id"),
            sender_kind=MSG_FROM_PM, body=payload.initial_message,
        ))
    await db.commit()
    await db.refresh(a)
    return _to_out(a)


@router.patch("/{assignment_id}", response_model=AssignmentOut)
async def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
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
    _: dict = Depends(require_role("admin", "lead")),
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


# ─── Engineer accept / reject ──────────────────────────────────────────

@router.post("/{assignment_id}/accept", response_model=AssignmentOut)
async def accept_assignment(
    assignment_id: int,
    payload: AssignmentAccept,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> AssignmentOut:
    if user.get("role") != ENGINEER_ROLE:
        raise HTTPException(status_code=403, detail="仅工程师可接单")
    a = await db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="派单不存在")
    if a.engineer_id != user.get("engineer_id"):
        raise HTTPException(status_code=403, detail="无权接受此派单")
    if a.approval_status != APPROVAL_PENDING:
        raise HTTPException(status_code=400, detail=f"派单当前状态 {a.approval_status}，不可重复操作")

    a.approval_status = APPROVAL_ACCEPTED
    a.engineer_responded_at = datetime.utcnow()
    body = (payload.note.strip() if payload.note else "") or "已接单。"
    db.add(AssignmentMessage(
        assignment_id=a.id, sender_user_id=user.get("user_id"),
        sender_kind=MSG_FROM_ENGINEER, body=f"✓ 接单：{body}",
    ))
    await db.commit()
    await db.refresh(a)
    return _to_out(a)


@router.post("/{assignment_id}/reject", response_model=AssignmentOut)
async def reject_assignment(
    assignment_id: int,
    payload: AssignmentReject,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> AssignmentOut:
    if user.get("role") != ENGINEER_ROLE:
        raise HTTPException(status_code=403, detail="仅工程师可拒单")
    a = await db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="派单不存在")
    if a.engineer_id != user.get("engineer_id"):
        raise HTTPException(status_code=403, detail="无权拒绝此派单")
    if a.approval_status != APPROVAL_PENDING:
        raise HTTPException(status_code=400, detail=f"派单当前状态 {a.approval_status}，不可重复操作")

    a.approval_status = APPROVAL_REJECTED
    a.engineer_responded_at = datetime.utcnow()
    db.add(AssignmentMessage(
        assignment_id=a.id, sender_user_id=user.get("user_id"),
        sender_kind=MSG_FROM_ENGINEER, body=f"✗ 拒单理由：{payload.reason.strip()}",
    ))
    await db.commit()
    await db.refresh(a)
    return _to_out(a)


# ─── Conversation reply (both sides) ───────────────────────────────────

@router.post("/{assignment_id}/messages", response_model=AssignmentMessageOut, status_code=status.HTTP_201_CREATED)
async def add_message(
    assignment_id: int,
    payload: AssignmentReply,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> AssignmentMessageOut:
    a = await db.get(Assignment, assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="派单不存在")
    await _assert_can_access_assignment(a, user)

    sender_kind = MSG_FROM_PM if user.get("role") in PM_ROLES else MSG_FROM_ENGINEER
    m = AssignmentMessage(
        assignment_id=a.id, sender_user_id=user.get("user_id"),
        sender_kind=sender_kind, body=payload.body.strip(),
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    sender_name = user.get("sub")
    return _msg_to_out(m, sender_name)
