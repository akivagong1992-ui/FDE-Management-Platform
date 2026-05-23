from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.expense import EXPENSE_STATUS_REJECTED, ExpenseRequest
from app.models.need_party import NeedParty
from app.models.project import (
    PROJECT_KIND_NO_REVENUE,
    VALUE_BASIS_OUTSOURCE_EQUIV,
    Project,
    SalesTransferLog,
)
from app.models.sales_person import SalesPerson
from app.models.user import User
from app.models.vendor_service_fee import VendorServiceFee
from app.schemas.project import (
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    SalesTransferLogOut,
    TransferSalesRequest,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _to_out(p: Project) -> ProjectOut:
    # Compute value_created for no_revenue projects (R13 auto-calc):
    # value_created = outsource_benchmark_amount (unless overridden in future)
    computed = None
    if p.kind == PROJECT_KIND_NO_REVENUE:
        computed = p.outsource_benchmark_amount
    return ProjectOut(
        id=p.id,
        code=p.code,
        name=p.name,
        need_party_id=p.need_party_id,
        need_party_name=p.need_party.name if p.need_party else None,
        sales_person_id=p.sales_person_id,
        sales_person_name=p.sales_person.name if p.sales_person else None,
        sales_person_active=p.sales_person.is_active if p.sales_person else None,
        pm_user_id=p.pm_user_id,
        kind=p.kind,
        outsource_benchmark_amount=p.outsource_benchmark_amount,
        value_created_basis=p.value_created_basis,
        value_created_note=p.value_created_note,
        value_created_computed=computed,
        status=p.status,
        planned_start_date=p.planned_start_date,
        planned_end_date=p.planned_end_date,
        actual_start_date=p.actual_start_date,
        actual_end_date=p.actual_end_date,
        description=p.description,
        district=p.district,
        rework_count=p.rework_count or 0,
        change_count=p.change_count or 0,
        renewal_of_project_id=p.renewal_of_project_id,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _validate_no_revenue_fields(kind: str, basis: str | None, note: str | None) -> None:
    if kind != PROJECT_KIND_NO_REVENUE:
        return
    if not basis:
        # Default basis if user prefers the simple checkbox flow (R13)
        return  # filled by caller with default
    if basis == "other" and not note:
        raise HTTPException(status_code=400, detail="value_created_basis=other 时必须填备注")


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    kind: str | None = None,
    status_filter: str | None = None,
    sales_person_id: int | None = None,
    need_party_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[ProjectOut]:
    stmt = select(Project).order_by(Project.id.desc())
    if kind:
        stmt = stmt.where(Project.kind == kind)
    if status_filter:
        stmt = stmt.where(Project.status == status_filter)
    if sales_person_id is not None:
        stmt = stmt.where(Project.sales_person_id == sales_person_id)
    if need_party_id is not None:
        stmt = stmt.where(Project.need_party_id == need_party_id)
    rows = (await db.execute(stmt)).scalars().all()
    return [_to_out(p) for p in rows]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> ProjectOut:
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="项目不存在")
    return _to_out(p)


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead", "pm")),
) -> ProjectOut:
    # 只有 lead/admin 才能创建 no_revenue 项目（R13 防滥用）
    if payload.kind == PROJECT_KIND_NO_REVENUE and user.get("role") not in {"admin", "lead"}:
        raise HTTPException(status_code=403, detail="仅团队负责人可创建无收入项目")

    if not await db.get(NeedParty, payload.need_party_id):
        raise HTTPException(status_code=400, detail="需求方不存在")
    sales = await db.get(SalesPerson, payload.sales_person_id)
    if not sales:
        raise HTTPException(status_code=400, detail="销售人员不存在")
    if not sales.is_active:
        raise HTTPException(status_code=400, detail="销售人员已停用，请选其他人")
    if payload.pm_user_id is not None and not await db.get(User, payload.pm_user_id):
        raise HTTPException(status_code=400, detail="PM 用户不存在")

    data = payload.model_dump()
    if payload.kind == PROJECT_KIND_NO_REVENUE and not data.get("value_created_basis"):
        data["value_created_basis"] = VALUE_BASIS_OUTSOURCE_EQUIV
    _validate_no_revenue_fields(payload.kind, data.get("value_created_basis"), data.get("value_created_note"))

    p = Project(**data)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _to_out(p)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead", "pm")),
) -> ProjectOut:
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="项目不存在")
    data = payload.model_dump(exclude_unset=True)

    # Changing kind requires lead
    if "kind" in data and data["kind"] != p.kind:
        if user.get("role") not in {"admin", "lead"}:
            raise HTTPException(status_code=403, detail="仅团队负责人可切换项目类型 (有收入↔无收入)")

    new_kind = data.get("kind", p.kind)
    new_basis = data.get("value_created_basis", p.value_created_basis)
    new_note = data.get("value_created_note", p.value_created_note)
    if new_kind == PROJECT_KIND_NO_REVENUE and not new_basis:
        data["value_created_basis"] = VALUE_BASIS_OUTSOURCE_EQUIV
        new_basis = VALUE_BASIS_OUTSOURCE_EQUIV
    _validate_no_revenue_fields(new_kind, new_basis, new_note)

    for k, v in data.items():
        setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    return _to_out(p)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead")),
) -> None:
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="项目不存在")
    await db.delete(p)
    await db.commit()


# ─── Transfer sales (R15) ──────────────────────────────────────────────

@router.post("/{project_id}/transfer-sales", response_model=ProjectOut)
async def transfer_sales(
    project_id: int,
    payload: TransferSalesRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin", "lead")),
) -> ProjectOut:
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="项目不存在")
    if payload.to_sales_person_id == p.sales_person_id:
        raise HTTPException(status_code=400, detail="目标销售与当前相同")
    new_sales = await db.get(SalesPerson, payload.to_sales_person_id)
    if not new_sales:
        raise HTTPException(status_code=400, detail="目标销售不存在")

    from_id = p.sales_person_id
    p.sales_person_id = payload.to_sales_person_id
    db.add(
        SalesTransferLog(
            project_id=p.id,
            from_sales_person_id=from_id,
            to_sales_person_id=payload.to_sales_person_id,
            reason=payload.reason,
            reason_note=payload.reason_note,
            operator_user_id=None,  # could resolve username→user lookup; left null for Phase 1b-i
        )
    )
    await db.commit()
    await db.refresh(p)
    return _to_out(p)


@router.get("/{project_id}/cost-breakdown")
async def cost_breakdown(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "lead", "finance")),
) -> dict:
    """项目成本归集（Phase 2a 版本）— Vendor 服务费 + 外部支出（已批准 / 已支付，不含驳回）。"""
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="项目不存在")

    # Vendor service fees on this project
    vsf_total = (await db.execute(
        select(func.coalesce(func.sum(VendorServiceFee.amount), 0))
        .where(VendorServiceFee.project_id == project_id)
    )).scalar_one()

    # External expenses (exclude rejected)
    expenses_total = (await db.execute(
        select(func.coalesce(func.sum(ExpenseRequest.amount), 0))
        .where(
            ExpenseRequest.project_id == project_id,
            ExpenseRequest.status != EXPENSE_STATUS_REJECTED,
        )
    )).scalar_one()

    # Break down by expense_type
    by_type_rows = (await db.execute(
        select(ExpenseRequest.expense_type, func.coalesce(func.sum(ExpenseRequest.amount), 0))
        .where(
            ExpenseRequest.project_id == project_id,
            ExpenseRequest.status != EXPENSE_STATUS_REJECTED,
        )
        .group_by(ExpenseRequest.expense_type)
    )).all()
    expenses_by_type = [{"type": t, "amount": float(amt)} for t, amt in by_type_rows]

    total = float(vsf_total) + float(expenses_total)
    return {
        "project_id": project_id,
        "project_name": p.name,
        "vendor_service_fees_total": float(vsf_total),
        "external_expenses_total": float(expenses_total),
        "external_expenses_by_type": expenses_by_type,
        "total_cost": total,
        "outsource_benchmark_amount": float(p.outsource_benchmark_amount) if p.outsource_benchmark_amount else None,
        "_note": "Phase 2a partial: 仅含 Vendor 服务费 + 外部支出；不含工时 × 单价。完整三口径见 Phase 2b。",
    }


@router.get("/{project_id}/transfer-logs", response_model=list[SalesTransferLogOut])
async def list_transfer_logs(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> list[SalesTransferLogOut]:
    stmt = (
        select(SalesTransferLog)
        .where(SalesTransferLog.project_id == project_id)
        .order_by(SalesTransferLog.id.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [SalesTransferLogOut.model_validate(r) for r in rows]
