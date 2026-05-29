"""Profit calculation service — three concurrent views (README §1.5).

A · Team overall margin (admin-web, lead/finance only — must be positive)
B · Sales-person × project / Client × project (admin-web, lead/finance only — can be negative)
C · Cockpit-facing savings + value_created (cockpit only — driven by outsource benchmark)
"""

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import EXPENSE_STATUS_PAID, ExpenseRequest
from app.models.need_party import NeedParty
from app.models.project import (
    PROJECT_BID_OUTCOME_WON,
    PROJECT_KIND_NO_REVENUE,
    PROJECT_KIND_REVENUE,
    PROJECT_STATUS_ACCEPTING,
    PROJECT_STATUS_ARCHIVED,
    PROJECT_STATUS_CANCELLED,
    Project,
)
from app.models.project_revenue import ProjectRevenue
from app.models.sales_person import SalesPerson
from app.models.vendor import Vendor
from app.models.vendor_service_fee import VendorServiceFee


ZERO = Decimal("0")


def _dec(x) -> Decimal:
    return Decimal(str(x)) if x is not None else ZERO


def _dec_or_none(x) -> Decimal | None:
    """与 _dec 不同：NULL 保留为 None，让调用方显式判断是否跳过聚合。
    用于 benchmark：缺失代表"没询价"，禁止当 0 计入对外口径（README §1.7.4）。
    """
    return Decimal(str(x)) if x is not None else None


# ── Cost helpers ───────────────────────────────────────────────────────

async def _project_costs(db: AsyncSession) -> dict[int, Decimal]:
    """Return {project_id: total_cost_in_HKD}. Cost = Vendor service fees + paid external expenses.

    口径 A/B 采用现金基础：只有 status=paid 的报销才计入成本，
    pending/approved 视为"未确定支出"，避免未审批的草稿单拉低毛利。
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
        .where(ExpenseRequest.status == EXPENSE_STATUS_PAID)
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
    """口径 A：团队真实利润 = Σ VSF − Σ 全部支出（vendor markup 视角）。

    ╔══════════════════════════════════════════════════════════════════╗
    ║  ⛔ 业务公式锁定（2026-05-28 用户 final 确认）                       ║
    ║                                                                  ║
    ║    team_revenue  ≈  Σ VSF        （pass-through invariant）       ║
    ║    team_margin   =  Σ VSF − Σ 全部支出（仅 paid）                  ║
    ║                                                                  ║
    ║  ❗ 修改前必须做的事：                                                ║
    ║    1. 反复跟 Akiva 确认 ≥ 3 次"真的要改吗"                          ║
    ║    2. 检查 tests/test_profit_overall_formula.py 是否同步更新        ║
    ║    3. 检查前端 OverallView.vue tooltip 是否同步更新                 ║
    ║    4. 检查 README §1.4 / §1.5 / PLAN.md 是否同步更新                ║
    ║                                                                  ║
    ║  历史教训：曾被错误改成 revenue − VSF − expenses（2026-05-28 上午），║
    ║  违反 pass-through 假设，又花一轮回滚。下次别再这么改。              ║
    ╚══════════════════════════════════════════════════════════════════╝

    业务模型（README §1.4 pass-through）：
      - 团队入账 100% pass-through 给 vendor → revenue ≈ VSF（应该相等）
      - vendor 用收到的 VSF 付：全部支出（含「外包工程师支出」新类目）
      - vendor 是受控壳；它自留的 markup = 团队真实利润
      - 公式：team_margin = VSF − Σ 全部支出
      - revenue 字段仅用于对账（VSF 录全后 revenue ≈ VSF）

    关键依赖：
      - "外包工程师支出" 类目必须录全，否则 team_margin 偏高
      - 现金基础：支出仅计 status=paid 的报销，pending/approved 不计入

    注意：revenue 这里仍然按 bid=won + kind=revenue 过滤——驾驶舱/对账时只看
    真正中标项目，避免投标中 / 跑单的虚假数据干扰对账。
    """
    revenue = (await db.execute(
        select(func.coalesce(func.sum(ProjectRevenue.amount), 0))
        .select_from(ProjectRevenue)
        .join(Project, Project.id == ProjectRevenue.project_id)
        .where(
            Project.kind == PROJECT_KIND_REVENUE,
            Project.bid_outcome == PROJECT_BID_OUTCOME_WON,
        )
    )).scalar_one()

    vendor_fees = (await db.execute(
        select(func.coalesce(func.sum(VendorServiceFee.amount), 0))
    )).scalar_one()

    # 按 vendor 拆分（KPI 卡片用，vendor 数 ≤ 3，直接列）
    vsf_per_vendor_rows = (await db.execute(
        select(
            VendorServiceFee.vendor_id,
            Vendor.name,
            func.coalesce(func.sum(VendorServiceFee.amount), 0),
        )
        .join(Vendor, Vendor.id == VendorServiceFee.vendor_id)
        .group_by(VendorServiceFee.vendor_id, Vendor.name)
        .order_by(func.sum(VendorServiceFee.amount).desc())
    )).all()
    vsf_by_vendor = [
        {"vendor_id": vid, "vendor_name": name, "amount": float(_dec(amt))}
        for vid, name, amt in vsf_per_vendor_rows
    ]

    expenses = (await db.execute(
        select(func.coalesce(func.sum(ExpenseRequest.amount), 0))
        .where(ExpenseRequest.status == EXPENSE_STATUS_PAID)
    )).scalar_one()

    revenue_d = _dec(revenue)
    fees_d = _dec(vendor_fees)
    exp_d = _dec(expenses)
    margin = fees_d - exp_d  # 口径 A：vendor markup = 团队真实利润
    return {
        "total_revenue": float(revenue_d),
        "total_vendor_service_fees": float(fees_d),
        "vsf_by_vendor": vsf_by_vendor,
        "total_external_expenses": float(exp_d),  # vendor 端全部支出（含外包工程师）
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
        has_benchmark = True
        if p.kind == PROJECT_KIND_REVENUE:
            revenue = revs.get(p.id, ZERO)
            cost = costs.get(p.id, ZERO)
        else:  # no_revenue — 用 benchmark 作为机会成本
            revenue = ZERO
            bench = _dec_or_none(p.outsource_benchmark_amount)
            if bench is None:
                # 没询价 → 机会成本未知，cost=0 保持聚合可加；前端识别 has_benchmark 显示"—"
                cost = ZERO
                has_benchmark = False
            else:
                cost = bench
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
            "has_benchmark": has_benchmark,
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
    skipped_missing_benchmark = 0
    for p in projects:
        bench = _dec_or_none(p.outsource_benchmark_amount)
        if bench is None:
            # 跳过没估过的项目——苹果对苹果原则。否则 bench=0 会让老外包毛利率看起来虚高，
            # 提升幅度被低估。计数透明告知。
            skipped_missing_benchmark += 1
            continue
        team_recv = team_rev.get(p.id, ZERO)
        gross_recv = gross_rev.get(p.id, team_recv)
        nse = non_service.get(p.id, ZERO)
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
        "skipped_missing_benchmark": skipped_missing_benchmark,
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
    skipped_rev_missing_benchmark = 0
    for p in rev_projects:
        bench = _dec_or_none(p.outsource_benchmark_amount)
        if bench is None:
            # 跳过：没估过外包报价 → savings 无法计算，否则会出现负数（=−team_share）拉低驾驶舱
            skipped_rev_missing_benchmark += 1
            continue
        team_share = team_revenue_by_pid.get(p.id, ZERO)
        savings += bench - team_share
        counted_revenue_projects += 1

    # 3) 无收入项目：必须已完成（accepting / archived），且非 cancelled
    no_rev_rows = (await db.execute(
        select(Project).where(
            Project.kind == PROJECT_KIND_NO_REVENUE,
            Project.status.in_([PROJECT_STATUS_ACCEPTING, PROJECT_STATUS_ARCHIVED]),
        )
    )).scalars().all()
    value_created = ZERO
    counted_no_rev_projects = 0
    skipped_no_rev_missing_benchmark = 0
    for p in no_rev_rows:
        bench = _dec_or_none(p.outsource_benchmark_amount)
        if bench is None:
            skipped_no_rev_missing_benchmark += 1
            continue
        value_created += bench
        counted_no_rev_projects += 1

    total_c = savings + value_created
    return {
        "savings_from_revenue_projects": float(savings),
        "value_created_from_no_revenue_projects": float(value_created),
        "total_c_view": float(total_c),
        # 信息透明：让前端能展示「N 个项目计入 / 总报价 M」给老板看
        "revenue_project_count": counted_revenue_projects,
        "no_revenue_project_count": counted_no_rev_projects,
        "skipped_revenue_missing_benchmark": skipped_rev_missing_benchmark,
        "skipped_no_revenue_missing_benchmark": skipped_no_rev_missing_benchmark,
        "currency": "HKD",
        # NOTE: by design this response carries NO field named like
        # "revenue", "cost", "margin", "team_margin", "vendor_fees" or similar
        # admin-grade A/B numbers. CI test asserts this.
    }
