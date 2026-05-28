from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.data_dict import DataDict
from app.models.engineer import Engineer
from app.models.expense import (
    APPROVAL_STAGE_LEAD,
    APPROVAL_STAGE_VENDOR,
    EXPENSE_STATUS_APPROVED,
    EXPENSE_STATUS_PAID,
    EXPENSE_STATUS_PENDING,
    EXPENSE_STATUS_REJECTED,
    ExpenseRequest,
)
from app.models.project import Project
from app.models.supplier import Supplier
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.expense import (
    ApprovalAction,
    ExpenseRequestCreate,
    ExpenseRequestOut,
    ExpenseRequestUpdate,
)

router = APIRouter(prefix="/expenses", tags=["expenses"])

PM_ROLES = {"admin", "lead", "pm", "finance"}  # 看全部 + 审批
ENGINEER_ROLE = "engineer"
VENDOR_ROLE = "vendor"  # 仅可提交 + 看自己 vendor 公司名下的


async def _vendor_name(db: AsyncSession, vid: int | None) -> str | None:
    if vid is None:
        return None
    v = await db.get(Vendor, vid)
    return v.name if v else None


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
        vendor_id=e.vendor_id,
        vendor_name=await _vendor_name(db, e.vendor_id),
        engineer_id=e.engineer_id,
        engineer_name=e.engineer.full_name if e.engineer else None,
        expense_type=e.expense_type,
        expense_type_label=await _label_for_type(db, e.expense_type),
        title=e.title,
        amount=e.amount,
        currency=e.currency,
        expense_date=e.expense_date,
        description=e.description,
        status=e.status,
        approval_stage=e.approval_stage,
        requested_by_user_id=e.requested_by_user_id,
        vendor_approved_by_user_id=e.vendor_approved_by_user_id,
        vendor_approved_at=e.vendor_approved_at,
        vendor_approval_note=e.vendor_approval_note,
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
    user: dict = Depends(get_current_user),
) -> list[ExpenseRequestOut]:
    stmt = select(ExpenseRequest).order_by(ExpenseRequest.id.desc())

    role = user.get("role")
    if role == ENGINEER_ROLE:
        # engineer 角色：只看自己提交的支出申请
        uid = user.get("user_id")
        if not uid:
            return []
        stmt = stmt.where(ExpenseRequest.requested_by_user_id == uid)
    elif role == VENDOR_ROLE:
        # vendor 角色：只看自己 vendor 公司提交的
        vid = user.get("vendor_id")
        if not vid:
            return []
        stmt = stmt.where(ExpenseRequest.vendor_id == vid)
    elif role not in PM_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

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
    user: dict = Depends(get_current_user),
) -> ExpenseRequestOut:
    # vendor 替工程师录入 / engineer 自己提交垫付报销；admin/lead/pm/finance 只审批
    role = user.get("role")
    if role not in (VENDOR_ROLE, ENGINEER_ROLE):
        raise HTTPException(status_code=403, detail="只有 vendor 或 engineer 可以提交支出申请")

    if not await db.get(Project, payload.project_id):
        raise HTTPException(status_code=400, detail="项目不存在")
    if payload.supplier_id is not None and not await db.get(Supplier, payload.supplier_id):
        raise HTTPException(status_code=400, detail="供应商不存在")
    if not await _label_for_type(db, payload.expense_type):
        raise HTTPException(status_code=400, detail=f"支出类型 '{payload.expense_type}' 不在字典中")

    if role == ENGINEER_ROLE:
        # 工程师自由选 vendor 报账；engineer_id 强制 = 本人
        engineer_id_from_jwt = user.get("engineer_id")
        if not engineer_id_from_jwt:
            raise HTTPException(status_code=400, detail="工程师账号未关联 engineer 档案，无法提交")
        if not await db.get(Engineer, engineer_id_from_jwt):
            raise HTTPException(status_code=400, detail="工程师档案不存在")
        if payload.vendor_id is None:
            raise HTTPException(status_code=400, detail="请选择本笔报销由哪个 vendor 公司经办")
        if not await db.get(Vendor, payload.vendor_id):
            raise HTTPException(status_code=400, detail="vendor 公司不存在")
        engineer_id = engineer_id_from_jwt
        vendor_id = payload.vendor_id
        approval_stage = APPROVAL_STAGE_VENDOR  # 等所选 vendor 先批
    else:  # VENDOR_ROLE
        vendor_id = user.get("vendor_id")
        if not vendor_id:
            raise HTTPException(status_code=400, detail="vendor 账号未挂 vendor 公司，无法提交")
        engineer_id = payload.engineer_id
        if engineer_id is not None:
            eng = await db.get(Engineer, engineer_id)
            if not eng:
                raise HTTPException(status_code=400, detail="工程师不存在")
            if eng.vendor_id != vendor_id:
                raise HTTPException(status_code=403, detail="不能为其他 vendor 公司的工程师提交报销")
        approval_stage = APPROVAL_STAGE_LEAD  # vendor 自提跳过 vendor 阶段

    e = ExpenseRequest(**payload.model_dump(), status=EXPENSE_STATUS_PENDING)
    e.requested_by_user_id = await _user_id_from_jwt(db, user)
    e.vendor_id = vendor_id
    e.engineer_id = engineer_id
    e.approval_stage = approval_stage
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return await _to_out(db, e)


@router.patch("/{eid}", response_model=ExpenseRequestOut)
async def update_expense(
    eid: int,
    payload: ExpenseRequestUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
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


def _check_stage_authority(e: ExpenseRequest, user: dict) -> None:
    """根据当前 approval_stage + 调用者 role 判断能否操作。否则 403。"""
    role = user.get("role")
    if e.approval_stage == APPROVAL_STAGE_VENDOR:
        # vendor 阶段：限 vendor 角色 + 必须是经办的 vendor 公司
        if role != VENDOR_ROLE:
            raise HTTPException(status_code=403, detail="vendor 阶段只能由经办 vendor 操作")
        if user.get("vendor_id") != e.vendor_id:
            raise HTTPException(status_code=403, detail="只能审批本 vendor 名下的报销")
    elif e.approval_stage == APPROVAL_STAGE_LEAD:
        if role not in {"admin", "lead", "finance"}:
            raise HTTPException(status_code=403, detail="lead 阶段限 admin/lead/finance 操作")
    else:
        raise HTTPException(status_code=400, detail=f"未知审批阶段 {e.approval_stage}")


@router.post("/{eid}/approve", response_model=ExpenseRequestOut)
async def approve_expense(
    eid: int,
    payload: ApprovalAction,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> ExpenseRequestOut:
    e = await db.get(ExpenseRequest, eid)
    if not e:
        raise HTTPException(status_code=404, detail="支出单不存在")
    if e.status != EXPENSE_STATUS_PENDING:
        raise HTTPException(status_code=400, detail=f"当前状态 {e.status} 不可批准")
    _check_stage_authority(e, user)

    now = datetime.utcnow()
    uid = await _user_id_from_jwt(db, user)
    if e.approval_stage == APPROVAL_STAGE_VENDOR:
        # vendor 批了 → 进入 lead 阶段，仍 pending
        e.vendor_approved_by_user_id = uid
        e.vendor_approved_at = now
        e.vendor_approval_note = payload.approval_note
        e.approval_stage = APPROVAL_STAGE_LEAD
    else:  # APPROVAL_STAGE_LEAD
        e.approved_by_user_id = uid
        e.approved_at = now
        e.approval_note = payload.approval_note
        e.status = EXPENSE_STATUS_APPROVED
    await db.commit()
    await db.refresh(e)
    return await _to_out(db, e)


@router.post("/{eid}/reject", response_model=ExpenseRequestOut)
async def reject_expense(
    eid: int,
    payload: ApprovalAction,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> ExpenseRequestOut:
    e = await db.get(ExpenseRequest, eid)
    if not e:
        raise HTTPException(status_code=404, detail="支出单不存在")
    if e.status != EXPENSE_STATUS_PENDING:
        raise HTTPException(status_code=400, detail=f"当前状态 {e.status} 不可驳回")
    _check_stage_authority(e, user)

    now = datetime.utcnow()
    uid = await _user_id_from_jwt(db, user)
    if e.approval_stage == APPROVAL_STAGE_VENDOR:
        # vendor 驳回 = 终态 rejected；记到 vendor_approved_* 字段
        e.vendor_approved_by_user_id = uid
        e.vendor_approved_at = now
        e.vendor_approval_note = payload.approval_note
    else:  # APPROVAL_STAGE_LEAD
        e.approved_by_user_id = uid
        e.approved_at = now
        e.approval_note = payload.approval_note
    e.status = EXPENSE_STATUS_REJECTED
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
