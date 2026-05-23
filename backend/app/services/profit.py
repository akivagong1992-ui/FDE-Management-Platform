"""Profit calculation service — three concurrent views (README §1.5).

A · Team overall margin (admin-web, lead/finance only — must be positive)
B · Sales-person × project / Client × project (admin-web, lead/finance only — can be negative)
C · Cockpit-facing savings + value_created (cockpit only — driven by outsource benchmark)
"""

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import EXPENSE_STATUS_REJECTED, ExpenseRequest
from app.models.need_party import NeedParty
from app.models.project import (
    PROJECT_KIND_NO_REVENUE,
    PROJECT_KIND_REVENUE,
    PROJECT_STATUS_ARCHIVED,
    PROJECT_STATUS_CANCELLED,
    PROJECT_STATUS_CLOSING,
    Project,
)
from app.models.project_revenue import REVENUE_STATUS_RECEIVED, ProjectRevenue
from app.models.sales_person import SalesPerson
from app.models.vendor_service_fee import VendorServiceFee


ZERO = Decimal("0")


def _dec(x) -> Decimal:
    return Decimal(str(x)) if x is not None else ZERO


# ── Cost helpers ───────────────────────────────────────────────────────

async def _project_costs(db: AsyncSession) -> dict[int, Decimal]:
    """Return {project_id: total_cost_in_HKD}. Cost = Vendor service fees + non-rejected external expenses."""
    costs: dict[int, Decimal] = defaultdict(lambda: ZERO)

    vsf_rows = (await db.execute(
        select(VendorServiceFee.project_id, func.coalesce(func.sum(VendorServiceFee.amount), 0))
        .where(VendorServiceFee.project_id.is_not(None))
        .group_by(VendorServiceFee.project_id)
    )).all()
    for pid, total in vsf_rows:
        costs[pid] += _dec(total)

    exp_rows = (await db.execute(
        select(ExpenseRequest.project_id, func.coalesce(func.sum(ExpenseRequest.amount), 0))
        .where(ExpenseRequest.status != EXPENSE_STATUS_REJECTED)
        .group_by(ExpenseRequest.project_id)
    )).all()
    for pid, total in exp_rows:
        costs[pid] += _dec(total)

    return costs


async def _project_revenues(db: AsyncSession) -> dict[int, Decimal]:
    """Return {project_id: total_revenue_in_HKD}. Only revenue-kind projects ever have entries."""
    rev: dict[int, Decimal] = defaultdict(lambda: ZERO)
    rows = (await db.execute(
        select(ProjectRevenue.project_id, func.coalesce(func.sum(ProjectRevenue.amount), 0))
        .group_by(ProjectRevenue.project_id)
    )).all()
    for pid, total in rows:
        rev[pid] += _dec(total)
    return rev


# ── 口径 A — team overall ──────────────────────────────────────────────

async def compute_overall(db: AsyncSession) -> dict:
    """口径 A：团队整体利润 = Σ 收入 − Σ Vendor 服务费 − Σ 外部支出。必为正数（内部对账）。"""
    revenue = (await db.execute(
        select(func.coalesce(func.sum(ProjectRevenue.amount), 0))
    )).scalar_one()

    vendor_fees = (await db.execute(
        select(func.coalesce(func.sum(VendorServiceFee.amount), 0))
    )).scalar_one()

    expenses = (await db.execute(
        select(func.coalesce(func.sum(ExpenseRequest.amount), 0))
        .where(ExpenseRequest.status != EXPENSE_STATUS_REJECTED)
    )).scalar_one()

    revenue_d = _dec(revenue)
    fees_d = _dec(vendor_fees)
    exp_d = _dec(expenses)
    margin = revenue_d - fees_d - exp_d
    return {
        "total_revenue": float(revenue_d),
        "total_vendor_service_fees": float(fees_d),
        "total_external_expenses": float(exp_d),
        "team_margin": float(margin),
        "currency": "HKD",
    }


# ── 口径 B — per-project margin + sales / client grouping ──────────────

async def compute_per_project(db: AsyncSession) -> list[dict]:
    """口径 B 底表：每个项目的 收入/成本/毛利。仅 revenue 类项目；no_revenue 不入 B 视图。"""
    costs = await _project_costs(db)
    revs = await _project_revenues(db)

    rows = (await db.execute(
        select(Project).where(Project.kind == PROJECT_KIND_REVENUE).order_by(Project.id)
    )).scalars().all()

    out = []
    for p in rows:
        revenue = revs.get(p.id, ZERO)
        cost = costs.get(p.id, ZERO)
        out.append({
            "project_id": p.id,
            "project_name": p.name,
            "project_code": p.code,
            "status": p.status,
            "sales_person_id": p.sales_person_id,
            "sales_person_name": p.sales_person.name if p.sales_person else None,
            "need_party_id": p.need_party_id,
            "need_party_name": p.need_party.name if p.need_party else None,
            "revenue": float(revenue),
            "cost": float(cost),
            "margin": float(revenue - cost),
        })
    return out


async def compute_by_sales_person(db: AsyncSession) -> list[dict]:
    """口径 B 汇总：按销售人员分组。"""
    per_proj = await compute_per_project(db)
    by_sp: dict[int, dict] = {}
    for row in per_proj:
        sid = row["sales_person_id"]
        if sid not in by_sp:
            by_sp[sid] = {
                "sales_person_id": sid,
                "sales_person_name": row["sales_person_name"],
                "project_count": 0,
                "revenue": 0.0,
                "cost": 0.0,
                "margin": 0.0,
                "projects": [],
            }
        e = by_sp[sid]
        e["project_count"] += 1
        e["revenue"] += row["revenue"]
        e["cost"] += row["cost"]
        e["margin"] += row["margin"]
        e["projects"].append(row)
    return sorted(by_sp.values(), key=lambda x: -x["margin"])


async def compute_by_need_party(db: AsyncSession) -> list[dict]:
    """口径 B 汇总：按客户/需求方分组。"""
    per_proj = await compute_per_project(db)
    by_np: dict[int, dict] = {}
    for row in per_proj:
        nid = row["need_party_id"]
        if nid not in by_np:
            by_np[nid] = {
                "need_party_id": nid,
                "need_party_name": row["need_party_name"],
                "project_count": 0,
                "revenue": 0.0,
                "cost": 0.0,
                "margin": 0.0,
                "projects": [],
            }
        e = by_np[nid]
        e["project_count"] += 1
        e["revenue"] += row["revenue"]
        e["cost"] += row["cost"]
        e["margin"] += row["margin"]
        e["projects"].append(row)
    return sorted(by_np.values(), key=lambda x: -x["margin"])


# ── 口径 C — savings + value_created (cockpit-only) ────────────────────

async def compute_cockpit_savings_and_value(db: AsyncSession) -> dict:
    """口径 C：仅在 *实际实现价值* 后才计入驾驶舱降本。

    收款门槛（方案 B）：
    ─ 有收入项目: 至少有 1 笔 ProjectRevenue.status='received'，且 status != cancelled。
                  effective_benchmark = min(outsource_benchmark, Σ 实收金额)；
                  savings = effective_benchmark − actual_cost。
                  实收 < 报价 时按实收封顶，避免虚高。
    ─ 无收入项目: status ∈ {closing, archived}（项目已完成）且 status != cancelled。
                  value_created = outsource_benchmark_amount（已封顶为完成标记）。

    驾驶舱专用接口。**禁止返回口径 A 或 B 的数字**（合规约束）。
    """
    costs = await _project_costs(db)

    # 1) 先汇总每个项目的实收金额（status=received 才算）
    received_rows = (await db.execute(
        select(ProjectRevenue.project_id, func.coalesce(func.sum(ProjectRevenue.amount), 0))
        .where(ProjectRevenue.status == REVENUE_STATUS_RECEIVED)
        .group_by(ProjectRevenue.project_id)
    )).all()
    received_by_pid: dict[int, Decimal] = {pid: _dec(amt) for pid, amt in received_rows}

    # 2) 有收入项目：实收门槛 + 报价封顶
    rev_rows = (await db.execute(
        select(Project).where(
            Project.kind == PROJECT_KIND_REVENUE,
            Project.status != PROJECT_STATUS_CANCELLED,
        )
    )).scalars().all()

    savings = ZERO
    counted_revenue_projects = 0
    for p in rev_rows:
        received = received_by_pid.get(p.id, ZERO)
        if received <= 0:
            continue  # 还没收到任何钱 → 不计入降本（避免虚报）
        bench = _dec(p.outsource_benchmark_amount)
        effective_bench = min(bench, received) if bench > 0 else received
        actual = costs.get(p.id, ZERO)
        savings += effective_bench - actual
        counted_revenue_projects += 1

    # 3) 无收入项目：必须已完成（closing / archived），且非 cancelled
    no_rev_rows = (await db.execute(
        select(Project).where(
            Project.kind == PROJECT_KIND_NO_REVENUE,
            Project.status.in_([PROJECT_STATUS_CLOSING, PROJECT_STATUS_ARCHIVED]),
        )
    )).scalars().all()
    value_created = sum((_dec(p.outsource_benchmark_amount) for p in no_rev_rows), ZERO)

    total_c = savings + value_created
    return {
        "savings_from_revenue_projects": float(savings),
        "value_created_from_no_revenue_projects": float(value_created),
        "total_c_view": float(total_c),
        # 信息透明：让前端能展示「N 个项目计入 / 总报价 M」给老板看
        "revenue_project_count": counted_revenue_projects,
        "no_revenue_project_count": len(no_rev_rows),
        "currency": "HKD",
        # NOTE: by design this response carries NO field named like
        # "revenue", "cost", "margin", "team_margin", "vendor_fees" or similar
        # admin-grade A/B numbers. CI test asserts this.
    }
