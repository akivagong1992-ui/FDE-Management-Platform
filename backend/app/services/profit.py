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
    PROJECT_BID_OUTCOME_WON,
    PROJECT_KIND_NO_REVENUE,
    PROJECT_KIND_REVENUE,
    PROJECT_STATUS_ARCHIVED,
    PROJECT_STATUS_CANCELLED,
    PROJECT_STATUS_CLOSING,
    Project,
)
from app.models.project_revenue import ProjectRevenue
from app.models.sales_person import SalesPerson
from app.models.vendor_service_fee import VendorServiceFee


ZERO = Decimal("0")


def _dec(x) -> Decimal:
    return Decimal(str(x)) if x is not None else ZERO


# ── Cost helpers ───────────────────────────────────────────────────────

async def _project_costs(db: AsyncSession) -> dict[int, Decimal]:
    """Return {project_id: total_cost_in_HKD}. Cost = Vendor service fees + non-rejected external expenses.

    用于口径 A / B（真实利润对账）。口径 C 用 _project_vsf() 即可——6 类支出
    本来就是 vendor 从团队入账的钱里支付，已含在 VSF，再减一次 = 重复扣除。
    """
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


async def _project_vsf(db: AsyncSession) -> dict[int, Decimal]:
    """Return {project_id: VSF_total_in_HKD}. 仅 Vendor 服务费，不含 6 类支出。

    口径 C 专用：钱流是 客户→团队→Vendor 100% pass-through，团队入账 ≈ VSF，
    Vendor 再用这笔钱付 6 类支出（材料/差旅/分包/许可/培训/其他）。
    所以「降本 = 报价 − 团队入账」= 报价 − VSF。
    """
    vsf: dict[int, Decimal] = defaultdict(lambda: ZERO)
    rows = (await db.execute(
        select(VendorServiceFee.project_id, func.coalesce(func.sum(VendorServiceFee.amount), 0))
        .where(VendorServiceFee.project_id.is_not(None))
        .group_by(VendorServiceFee.project_id)
    )).all()
    for pid, total in rows:
        vsf[pid] += _dec(total)
    return vsf


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
    """口径 A：团队整体利润 = Σ 团队入账 − Σ VSF。

    业务模型（用户确认）：VSF 已包含 6 类支出（vendor 用团队入账的钱内部消化），
    所以 margin 公式里只减 VSF，不再单独减 6 类——否则双重扣减。
    `total_external_expenses` 字段保留供 UI 作为参考信息展示（vendor 端支出明细快照），
    但**不参与 team_margin 计算**。
    """
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
    margin = revenue_d - fees_d
    return {
        "total_revenue": float(revenue_d),
        "total_vendor_service_fees": float(fees_d),
        "total_external_expenses": float(exp_d),  # 仅展示 / vendor 端支出快照
        "team_margin": float(margin),
        "currency": "HKD",
    }


# ── 口径 B — per-project margin + sales / client grouping ──────────────

async def compute_per_project(db: AsyncSession) -> list[dict]:
    """口径 B 底表：每个项目的 收入/成本/毛利。

    revenue 项目：
        收入 = Σ ProjectRevenue.amount（团队入账）
        成本 = Σ VSF（已含 6 类支出，与 compute_overall 同口径）
    no_revenue 项目（业务模型修正）：
        工程师在 pre-sales / 内部咨询阶段已经投入了精力，即使没有客户收入也要守这笔机会成本。
        收入 = 0
        成本 = outsource_benchmark_amount（外部服务商报价当作机会成本估值）
        毛利 = −benchmark（负数，反映「无收入项目吃掉的预期外包成本」）
    """
    costs = await _project_vsf(db)
    revs = await _project_revenues(db)

    rows = (await db.execute(select(Project).order_by(Project.id))).scalars().all()

    out = []
    for p in rows:
        if p.kind == PROJECT_KIND_REVENUE:
            revenue = revs.get(p.id, ZERO)
            cost = costs.get(p.id, ZERO)
        else:  # no_revenue — 用 benchmark 作为机会成本
            revenue = ZERO
            cost = _dec(p.outsource_benchmark_amount)
        out.append({
            "project_id": p.id,
            "project_name": p.name,
            "project_code": p.code,
            "kind": p.kind,
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

async def compute_company_margin_lift(db: AsyncSession) -> dict:
    """公司级利润率提升（admin lead/finance 专享，**绝不进驾驶舱**）。

    公式（用户 2026-05-24 校准，含非服务开销）：
      老外包模式毛利率 = (客户付款 − 外部服务商报价 − 非服务开销) / 客户付款
      FDE 模式毛利率   = (客户付款 − 团队入账 − 非服务开销) / 客户付款
      利润率提升       = FDE − 老外包 = (外部服务商报价 − 团队入账) / 客户付款

    门槛：Project.bid_outcome == 'won'（投标已中标）。
      lost / escaped / pending → 不计入
      gross = Σ ProjectRevenue.gross_amount（必填）
      non_service = Σ ProjectRevenue.non_service_expense（硬件 / 第三方 / 物料）
      bench = Σ Project.outsource_benchmark_amount
      team_rev = Σ ProjectRevenue.amount（FDE 模式实际成本）
    """
    rev_rows = (await db.execute(
        select(
            ProjectRevenue.project_id,
            func.coalesce(func.sum(ProjectRevenue.amount), 0),
            func.coalesce(func.sum(
                func.coalesce(ProjectRevenue.gross_amount, ProjectRevenue.amount)
            ), 0),
            func.coalesce(func.sum(
                func.coalesce(ProjectRevenue.non_service_expense, 0)
            ), 0),
        )
        .group_by(ProjectRevenue.project_id)
    )).all()
    team_rev: dict[int, Decimal] = {pid: _dec(amt) for pid, amt, _, _ in rev_rows}
    gross_rev: dict[int, Decimal] = {pid: _dec(gross) for pid, _, gross, _ in rev_rows}
    non_service: dict[int, Decimal] = {pid: _dec(nse) for pid, _, _, nse in rev_rows}

    # 仅 bid_outcome=won 的 revenue 类项目
    projects = (await db.execute(
        select(Project).where(
            Project.kind == PROJECT_KIND_REVENUE,
            Project.bid_outcome == PROJECT_BID_OUTCOME_WON,
        )
    )).scalars().all()

    total_gross = ZERO
    total_team = ZERO
    total_benchmark = ZERO
    total_actual = ZERO
    total_non_service = ZERO
    counted = 0
    for p in projects:
        team_recv = team_rev.get(p.id, ZERO)
        gross_recv = gross_rev.get(p.id, team_recv)
        nse = non_service.get(p.id, ZERO)
        bench = _dec(p.outsource_benchmark_amount)
        total_gross += gross_recv
        total_team += team_recv
        total_benchmark += bench
        total_actual += team_recv
        total_non_service += nse
        counted += 1

    if total_gross > 0:
        outsource_margin = total_gross - total_benchmark - total_non_service
        fde_margin = total_gross - total_actual - total_non_service
        outsource_margin_pct = outsource_margin / total_gross * 100
        fde_margin_pct = fde_margin / total_gross * 100
        margin_lift_pct = fde_margin_pct - outsource_margin_pct
    else:
        outsource_margin = ZERO
        fde_margin = ZERO
        outsource_margin_pct = ZERO
        fde_margin_pct = ZERO
        margin_lift_pct = ZERO

    extra_profit = total_benchmark - total_actual  # = vendor markup absorbed (与 non_service 无关)

    return {
        "counted_projects": counted,
        "total_gross_revenue": float(total_gross),
        "total_team_revenue": float(total_team),
        "total_outsource_benchmark": float(total_benchmark),
        "total_actual_cost": float(total_actual),
        "total_non_service_expense": float(total_non_service),
        "outsource_margin": float(outsource_margin),
        "fde_margin": float(fde_margin),
        "outsource_margin_pct": float(outsource_margin_pct),
        "fde_margin_pct": float(fde_margin_pct),
        "margin_lift_pct": float(margin_lift_pct),
        "extra_profit": float(extra_profit),
        "currency": "HKD",
    }


async def compute_cockpit_savings_and_value(db: AsyncSession) -> dict:
    """口径 C：用户公式 `创造价值 = 外包估算 − 团队入账`。

    门槛（用户最新业务模型）：
    ─ 有收入项目: Project.bid_outcome == 'won'（已中标，团队默认一定拿到 team revenue）。
                  savings = outsource_benchmark − Σ ProjectRevenue.amount
                  不再 filter status=received（已中标即视作已实现）。
    ─ 无收入项目: status ∈ {closing, archived}（项目已完成）且 status != cancelled。
                  value_created = outsource_benchmark_amount。

    驾驶舱专用接口。**禁止返回口径 A 或 B 的数字**（合规约束）。
    """
    # 1) 每项目累计团队入账（不再 filter status — 默认中标 = 团队拿到）
    rev_rows = (await db.execute(
        select(ProjectRevenue.project_id, func.coalesce(func.sum(ProjectRevenue.amount), 0))
        .group_by(ProjectRevenue.project_id)
    )).all()
    team_revenue_by_pid: dict[int, Decimal] = {pid: _dec(amt) for pid, amt in rev_rows}

    # 2) 有收入项目：bid_outcome=won
    rev_projects = (await db.execute(
        select(Project).where(
            Project.kind == PROJECT_KIND_REVENUE,
            Project.bid_outcome == PROJECT_BID_OUTCOME_WON,
        )
    )).scalars().all()

    savings = ZERO
    counted_revenue_projects = 0
    for p in rev_projects:
        bench = _dec(p.outsource_benchmark_amount)
        team_share = team_revenue_by_pid.get(p.id, ZERO)
        savings += bench - team_share
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
