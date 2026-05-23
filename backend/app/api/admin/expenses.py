from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.data_dict import DataDict
from app.models.expense import (
    EXPENSE_STATUS_APPROVED,
    EXPENSE_STATUS_PAID,
    EXPENSE_STATUS_PENDING,
    EXPENSE_STATUS_REJECTED,
    ExpenseRequest,
)
from app.models.project import Project
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.expense import (
    ApprovalAction,
    ExpenseRequestCreate,
    ExpenseRequestOut,
    ExpenseRequestUpdate,
)

router = APIRouter(prefix="/expenses", tags=["expenses"])


async def _label_for_type(db: AsyncSession, code: str) -> str | None:
    row = (
        await db.execute(
            select(DataDict).where(DataDict.category == "expense_type", DataDict.code == code)
        )
    ).scalar_one_or_none()
    return row.label if row else None


async def _user_id_from_jwt(db: AsyncSession, user: dict) -> int | None:
    username = user.get("sub")
    if not username:
        return None
    u = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    return u.id if u else None


async def _to_out(db: AsyncSession, e: ExpenseRequest) -> ExpenseRequestOut:
    return ExpenseRequestOut(
        id=e.id,
        project_id=e.project_id,
        project_name=e.project.name if e.project else None,
        supplier_id=e.supplier_id,
        supplier_name=e.supplier.name if e.supplier else None,
        expense_type=e.expense_type,
        expense_type_label=await _label_for_type(db, e.expense_type),
        title=e.title,
        amount=e.amount,
        currency=e.currency,
        expense_date=e.expense_date,
        description=e.description,
        status=e.status,
        requested_by_user_id=e.requested_by_user_id,
        approved_by_user_id=e.approved_by_user_id,
        approved_at=e.approved_at,
        approval_note=e.approval_note,
        paid_at=e.paid_at,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


@router.get("", response_model=list[ExpenseRequestOut])
async def list_expenses(
    project_id: int | None = None,
    expense_type: str | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[ExpenseRequestOut]:
    stmt = select(ExpenseRequest).order_by(ExpenseRequest.id.desc())
    if project_id is not None:
        stmt = stmt.where(ExpenseRequest.project_id == project_id)
    if expense_type:
        stmt = stmt.where(ExpenseRequest.expense_type == expense_type)
    if status_filter:
        stmt = stmt.where(ExpenseRequest.status == status_filter)
    rows = (await db.execute(stmt)).scalars().all()
    return [await _to_out(db, e) for e in rows]


@router.post("", response_model=ExpenseRequestOut, status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: ExpenseRequestCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> ExpenseRequestOut:
    if not await db.get(Project, payload.project_id):
        raise HTTPException(status_code=400, detail="项目不存在")
    if payload.supplier_id is not None and not await db.get(Supplier, payload.supplier_id):
        raise HTTPException(status_code=400, detail="供应商不存在")
    if not await _label_for_type(db, payload.expense_type):
        raise HTTPException(status_code=400, detail=f"支出类型 '{payload.expense_type}' 不在字典中")

    e = ExpenseRequest(**payload.model_dump(), status=EXPENSE_STATUS_PENDING)
    e.requested_by_user_id = await _user_id_from_jwt(db, user)
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return await _to_out(db, e)


@router.patch("/{eid}", response_model=ExpenseRequestOut)
async def update_expense(
    eid: int,
    payload: ExpenseRequestUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "pm", "finance")),
) -> ExpenseRequestOut:
    e = await db.get(ExpenseRequest, eid)
    if not e:
        raise HTTPException(status_code=404, detail="支出单不存在")
    if e.status in {EXPENSE_STATUS_APPROVED, EXPENSE_STATUS_PAID}:
        raise HTTPException(status_code=400, detail="已批准/已支付的支出单不可修改；如需作废请先驳回")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(e, k, v)
    await db.commit()
    await db.refresh(e)
    return await _to_out(db, e)


@router.post("/{eid}/approve", response_model=ExpenseRequestOut)
async def approve_expense(
    eid: int,
    payload: ApprovalAction,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead", "finance")),
) -> ExpenseRequestOut:
    e = await db.get(ExpenseRequest, eid)
    if not e:
        raise HTTPException(status_code=404, detail="支出单不存在")
    if e.status != EXPENSE_STATUS_PENDING:
        raise HTTPException(status_code=400, detail=f"当前状态 {e.status} 不可批准")
    e.status = EXPENSE_STATUS_APPROVED
    e.approved_by_user_id = await _user_id_from_jwt(db, user)
    e.approved_at = datetime.utcnow()
    e.approval_note = payload.approval_note
    await db.commit()
    await db.refresh(e)
    return await _to_out(db, e)


@router.post("/{eid}/reject", response_model=ExpenseRequestOut)
async def reject_expense(
    eid: int,
    payload: ApprovalAction,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead", "finance")),
) -> ExpenseRequestOut:
    e = await db.get(ExpenseRequest, eid)
    if not e:
        raise HTTPException(status_code=404, detail="支出单不存在")
    if e.status != EXPENSE_STATUS_PENDING:
        raise HTTPException(status_code=400, detail=f"当前状态 {e.status} 不可驳回")
    e.status = EXPENSE_STATUS_REJECTED
    e.approved_by_user_id = await _user_id_from_jwt(db, user)
    e.approved_at = datetime.utcnow()
    e.approval_note = payload.approval_note
    await db.commit()
    await db.refresh(e)
    return await _to_out(db, e)


@router.post("/{eid}/mark-paid", response_model=ExpenseRequestOut)
async def mark_paid(
    eid: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> ExpenseRequestOut:
    e = await db.get(ExpenseRequest, eid)
    if not e:
        raise HTTPException(status_code=404, detail="支出单不存在")
    if e.status != EXPENSE_STATUS_APPROVED:
        raise HTTPException(status_code=400, detail="仅已批准状态可标记为已支付")
    e.status = EXPENSE_STATUS_PAID
    e.paid_at = datetime.utcnow()
    await db.commit()
    await db.refresh(e)
    return await _to_out(db, e)


@router.delete("/{eid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    eid: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    e = await db.get(ExpenseRequest, eid)
    if not e:
        raise HTTPException(status_code=404, detail="支出单不存在")
    await db.delete(e)
    await db.commit()
