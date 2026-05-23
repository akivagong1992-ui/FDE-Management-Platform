"""驾驶舱聚合接口集合（Tab 2/3/4/5/7/8 数据源）。

⚠️ 所有响应字段名严禁出现 team_margin / revenue / real_cost 等口径 A/B 关键字
   （由 tests/test_cockpit_isolation.py 强制 CI 守门）。
"""

from collections import defaultdict
from datetime import date as date_cls
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.assignment import ASSIGNMENT_STATUS_ENDED, Assignment
from app.models.engineer import Certificate, Engineer
from app.models.expense import EXPENSE_STATUS_REJECTED, ExpenseRequest
from app.models.need_party import NeedParty
from app.models.project import (
    PROJECT_KIND_NO_REVENUE,
    PROJECT_KIND_REVENUE,
    PROJECT_STATUS_ARCHIVED,
    PROJECT_STATUS_CLOSING,
    Project,
)
from app.models.renewal_attempt import (
    RENEWAL_OUTCOME_LOST,
    RENEWAL_OUTCOME_PENDING,
    RENEWAL_OUTCOME_WON,
    RenewalAttempt,
)
from app.models.retrospective import ProjectRetrospective
from app.models.skill import EngineerSkill, Skill
from app.models.vendor import Vendor
from app.models.vendor_service_fee import VendorServiceFee

router = APIRouter(tags=["cockpit-aggregations"])


# Shared cost lookup (reused; keep in sync with services/profit._project_costs)
async def _project_costs(db: AsyncSession) -> dict[int, float]:
    costs: dict[int, float] = defaultdict(float)
    vsf_rows = (await db.execute(
        select(VendorServiceFee.project_id, func.coalesce(func.sum(VendorServiceFee.amount), 0))
        .where(VendorServiceFee.project_id.is_not(None))
        .group_by(VendorServiceFee.project_id)
    )).all()
    for pid, total in vsf_rows:
        costs[pid] += float(total)
    exp_rows = (await db.execute(
        select(ExpenseRequest.project_id, func.coalesce(func.sum(ExpenseRequest.amount), 0))
        .where(ExpenseRequest.status != EXPENSE_STATUS_REJECTED)
        .group_by(ExpenseRequest.project_id)
    )).all()
    for pid, total in exp_rows:
        costs[pid] += float(total)
    return costs


# ── Tab 2 · Project board ───────────────────────────────────────────

@router.get("/project-board")
async def project_board(db: AsyncSession = Depends(get_db)) -> dict:
    """项目看板 — by_district 用于 Tab 2 HK 简图。"""
    rows = (await db.execute(select(Project).order_by(Project.id.desc()))).scalars().all()
    items = [
        {
            "project_id": p.id,
            "name": p.name,
            "code": p.code,
            "kind": p.kind,
            "status": p.status,
            "district": p.district,
            "need_party": p.need_party.name if p.need_party else None,
            "sales_person": p.sales_person.name if p.sales_person else None,
            "planned_start": str(p.planned_start_date) if p.planned_start_date else None,
            "planned_end": str(p.planned_end_date) if p.planned_end_date else None,
        }
        for p in rows
    ]
    # district aggregation with localized labels
    DISTRICT_LABELS = {
        "HK_ISLAND": "港岛", "KOWLOON": "九龙", "NT_EAST": "新界东",
        "NT_WEST": "新界西", "OUTLYING": "离岛",
    }
    district_counts: dict[str, int] = defaultdict(int)
    for it in items:
        district_counts[it.get("district") or "UNKNOWN"] += 1
    by_district = [
        {"code": code, "label": DISTRICT_LABELS.get(code, code), "count": cnt}
        for code, cnt in district_counts.items()
    ]
    by_district.sort(key=lambda x: -x["count"])
    return {
        "total": len(items),
        "by_status": _count_by(items, "status"),
        "by_district": by_district,
        "items": items[:24],
    }


# ── Tab 3 · Profit compare (extends Tier C; no money A/B fields) ────

@router.get("/profit-compare")
async def profit_compare(db: AsyncSession = Depends(get_db)) -> dict:
    """口径 C 扩展：节省 vs 创造价值 + Top 项目 + Vendor 节省贡献榜。"""
    costs = await _project_costs(db)

    rev_projects = (await db.execute(
        select(Project).where(Project.kind == PROJECT_KIND_REVENUE)
    )).scalars().all()
    no_rev_projects = (await db.execute(
        select(Project).where(Project.kind == PROJECT_KIND_NO_REVENUE)
    )).scalars().all()

    # Top savings on revenue projects
    rev_with_savings = []
    for p in rev_projects:
        bench = float(p.outsource_benchmark_amount or 0)
        actual = costs.get(p.id, 0.0)
        savings = bench - actual
        rev_with_savings.append({
            "project_id": p.id, "name": p.name,
            "savings": savings,
            "benchmark": bench,
            "actual": actual,
        })
    rev_with_savings.sort(key=lambda x: -x["savings"])

    # Top value_created on no-revenue projects
    no_rev_with_value = sorted(
        [
            {"project_id": p.id, "name": p.name, "value_created": float(p.outsource_benchmark_amount or 0)}
            for p in no_rev_projects
        ],
        key=lambda x: -x["value_created"],
    )

    # Vendor contribution — split each project's savings PROPORTIONAL to each
    # vendor's actual service-fee share on that project. Avoids double-counting
    # when multiple vendors collaborate on the same project.
    vendor_savings: dict[int, float] = defaultdict(float)
    vsf_per_project = (await db.execute(
        select(VendorServiceFee.vendor_id, VendorServiceFee.project_id,
               func.sum(VendorServiceFee.amount))
        .where(VendorServiceFee.project_id.is_not(None))
        .group_by(VendorServiceFee.vendor_id, VendorServiceFee.project_id)
    )).all()
    project_vendor_amounts: dict[int, dict[int, float]] = defaultdict(dict)
    for vid, pid, amt in vsf_per_project:
        project_vendor_amounts[pid][vid] = float(amt)

    proj_savings_lookup = {p["project_id"]: p["savings"] for p in rev_with_savings}
    for pid, vendor_amounts in project_vendor_amounts.items():
        if pid not in proj_savings_lookup:
            continue
        total = sum(vendor_amounts.values())
        if total <= 0:
            continue
        savings = proj_savings_lookup[pid]
        for vid, amt in vendor_amounts.items():
            vendor_savings[vid] += savings * (amt / total)

    vendor_names = {v.id: v.name for v in (await db.execute(select(Vendor))).scalars().all()}
    vendor_rank = sorted(
        [{"vendor_id": vid, "name": vendor_names.get(vid, f"#{vid}"), "savings": amt}
         for vid, amt in vendor_savings.items() if amt > 0],
        key=lambda x: -x["savings"],
    )

    total_savings = sum(p["savings"] for p in rev_with_savings)
    total_value_created = sum(p["value_created"] for p in no_rev_with_value)

    return {
        "total_savings": total_savings,
        "total_value_created": total_value_created,
        "total_c_view": total_savings + total_value_created,
        "top_savings_projects": rev_with_savings[:5],
        "top_value_projects": no_rev_with_value[:5],
        "vendor_contribution_rank": vendor_rank[:5],
    }


# ── Tab 4 · Engineer stats ──────────────────────────────────────────

@router.get("/engineer-stats")
async def engineer_stats(db: AsyncSession = Depends(get_db)) -> dict:
    engineers = (await db.execute(select(Engineer))).scalars().all()
    total = len(engineers)
    active = sum(1 for e in engineers if e.status == "active")

    # By Vendor distribution
    vendor_names = {v.id: v.name for v in (await db.execute(select(Vendor))).scalars().all()}
    by_vendor: dict[int, int] = defaultdict(int)
    for e in engineers:
        by_vendor[e.vendor_id] += 1
    vendor_dist = [
        {"vendor_id": vid, "name": vendor_names.get(vid, f"#{vid}"), "count": c}
        for vid, c in by_vendor.items()
    ]
    vendor_dist.sort(key=lambda x: -x["count"])

    # By level
    by_level: dict[int, int] = defaultdict(int)
    for e in engineers:
        by_level[e.level or 0] += 1
    level_dist = sorted(
        [{"level": lvl, "count": c} for lvl, c in by_level.items()],
        key=lambda x: x["level"],
    )

    # Top allocation — sum allocation_ratio of in-progress assignments
    alloc_rows = (await db.execute(
        select(Assignment.engineer_id, func.coalesce(func.sum(Assignment.allocation_ratio), 0))
        .where(Assignment.status != ASSIGNMENT_STATUS_ENDED)
        .group_by(Assignment.engineer_id)
    )).all()
    eng_name = {e.id: e.full_name for e in engineers}
    top_allocated = sorted(
        [{"engineer_id": eid, "name": eng_name.get(eid, f"#{eid}"), "alloc_pct": int(total)}
         for eid, total in alloc_rows],
        key=lambda x: -x["alloc_pct"],
    )[:5]

    return {
        "total": total,
        "active": active,
        "by_vendor": vendor_dist,
        "by_level": level_dist,
        "top_allocated": top_allocated,
    }


# ── Tab 5 · Efficiency ──────────────────────────────────────────────

@router.get("/efficiency-stats")
async def efficiency_stats(db: AsyncSession = Depends(get_db)) -> dict:
    projects = (await db.execute(select(Project))).scalars().all()
    total = len(projects)

    # On-time = projects with both planned_end and actual_end, where actual <= planned
    finished_with_dates = [
        p for p in projects
        if p.status in {PROJECT_STATUS_CLOSING, PROJECT_STATUS_ARCHIVED}
        and p.planned_end_date and p.actual_end_date
    ]
    on_time = [p for p in finished_with_dates if p.actual_end_date <= p.planned_end_date]
    on_time_rate = (len(on_time) / len(finished_with_dates)) if finished_with_dates else 0.0

    # By-status counts
    by_status = _count_by([{"status": p.status} for p in projects], "status")

    # Top recent completions
    recent_completed = sorted(
        [p for p in projects if p.actual_end_date],
        key=lambda p: p.actual_end_date or date_cls(1970, 1, 1),
        reverse=True,
    )[:5]
    recent_items = [
        {
            "project_id": p.id, "name": p.name,
            "planned_end": str(p.planned_end_date) if p.planned_end_date else None,
            "actual_end": str(p.actual_end_date),
            "on_time": bool(p.planned_end_date and p.actual_end_date <= p.planned_end_date),
        }
        for p in recent_completed
    ]

    # Rework / change stats (Phase 3-next-ii)
    total_rework = sum((p.rework_count or 0) for p in projects)
    total_change = sum((p.change_count or 0) for p in projects)
    projects_with_rework = sum(1 for p in projects if (p.rework_count or 0) > 0)
    rework_rate = (projects_with_rework / total) if total else 0.0
    avg_change_per_project = (total_change / total) if total else 0.0
    clean_delivery_count = sum(
        1 for p in projects if p.status == PROJECT_STATUS_ARCHIVED
        and (p.rework_count or 0) == 0 and (p.change_count or 0) <= 1
    )

    return {
        "total_projects": total,
        "finished_with_dates": len(finished_with_dates),
        "on_time_count": len(on_time),
        "on_time_rate": round(on_time_rate, 4),
        "by_status": by_status,
        "recent_completions": recent_items,
        "total_rework_count": total_rework,
        "total_change_count": total_change,
        "rework_rate": round(rework_rate, 4),
        "avg_changes_per_project": round(avg_change_per_project, 2),
        "clean_delivery_count": clean_delivery_count,
    }


# ── Tab 7 · Capability ──────────────────────────────────────────────

@router.get("/capability-stats")
async def capability_stats(db: AsyncSession = Depends(get_db)) -> dict:
    # Certificates
    certs = (await db.execute(select(Certificate))).scalars().all()
    by_issuer: dict[str, int] = defaultdict(int)
    for c in certs:
        by_issuer[(c.issuer or "其他")] += 1
    issuer_list = sorted(
        [{"issuer": k, "count": v} for k, v in by_issuer.items()], key=lambda x: -x["count"]
    )[:8]

    # Skill heatmap: skill_category × count of engineers
    skills = {s.id: s for s in (await db.execute(select(Skill))).scalars().all()}
    eng_skills = (await db.execute(select(EngineerSkill))).scalars().all()
    by_cat_level: dict[tuple[str, int], int] = defaultdict(int)
    for es in eng_skills:
        s = skills.get(es.skill_id)
        if not s:
            continue
        by_cat_level[(s.category, es.level)] += 1
    heatmap = [
        {"category": cat, "level": lvl, "count": cnt}
        for (cat, lvl), cnt in sorted(by_cat_level.items())
    ]

    # Top engineers by cert count
    eng_cert_count: dict[int, int] = defaultdict(int)
    for c in certs:
        eng_cert_count[c.engineer_id] += 1
    eng = {e.id: e.full_name for e in (await db.execute(select(Engineer))).scalars().all()}
    top_certified = sorted(
        [{"engineer_id": eid, "name": eng.get(eid, f"#{eid}"), "cert_count": cnt}
         for eid, cnt in eng_cert_count.items()],
        key=lambda x: -x["cert_count"],
    )[:5]

    return {
        "total_certificates": len(certs),
        "by_issuer": issuer_list,
        "skill_heatmap": heatmap,
        "top_certified_engineers": top_certified,
    }


# ── Tab 8 · Relationship ────────────────────────────────────────────

@router.get("/relationship-stats")
async def relationship_stats(db: AsyncSession = Depends(get_db)) -> dict:
    retros = (await db.execute(select(ProjectRetrospective))).scalars().all()
    if retros:
        avg_score = round(sum(r.satisfaction_score for r in retros) / len(retros), 2)
        closed = sum(1 for r in retros if r.is_closed)
        action_closure_rate = round(closed / len(retros), 4)
    else:
        avg_score = 0.0
        closed = 0
        action_closure_rate = 0.0

    # Renewal-rate proxy: NeedParties with ≥2 projects / those with ≥1 project
    np_rows = (await db.execute(
        select(Project.need_party_id, func.count(Project.id))
        .group_by(Project.need_party_id)
    )).all()
    total_clients = len(np_rows)
    repeat_clients = sum(1 for _, cnt in np_rows if cnt >= 2)
    renewal_rate = round(repeat_clients / total_clients, 4) if total_clients else 0.0

    # Top need parties by project count
    np_lookup = {n.id: n.name for n in (await db.execute(select(NeedParty))).scalars().all()}
    top_clients = sorted(
        [{"need_party_id": nid, "name": np_lookup.get(nid, f"#{nid}"), "project_count": cnt}
         for nid, cnt in np_rows],
        key=lambda x: -x["project_count"],
    )[:5]

    # True renewal — projects explicitly linked via renewal_of_project_id (Phase 3-next-ii)
    total_proj_count = (await db.execute(select(func.count(Project.id)))).scalar_one() or 0
    renewed_count = (await db.execute(
        select(func.count(Project.id)).where(Project.renewal_of_project_id.is_not(None))
    )).scalar_one() or 0
    true_renewal_rate = round(renewed_count / total_proj_count, 4) if total_proj_count else 0.0

    # Renewal-attempt funnel (Phase 3-next-iii Round 2)
    attempts = (await db.execute(select(RenewalAttempt))).scalars().all()
    won_count = sum(1 for a in attempts if a.outcome == RENEWAL_OUTCOME_WON)
    lost_count = sum(1 for a in attempts if a.outcome == RENEWAL_OUTCOME_LOST)
    pending_count = sum(1 for a in attempts if a.outcome == RENEWAL_OUTCOME_PENDING)
    win_denominator = won_count + lost_count
    win_rate = (won_count / win_denominator) if win_denominator > 0 else 0.0

    LOST_REASON_LABELS = {
        "lost_to_outsource": "输给传统外包",
        "price": "价格因素",
        "quality": "质量 / 满意度",
        "no_budget": "客户无预算",
        "internal_hire": "客户自建团队",
        "other": "其他",
    }
    reason_counts: dict[str, int] = defaultdict(int)
    for a in attempts:
        if a.outcome == RENEWAL_OUTCOME_LOST and a.lost_reason:
            reason_counts[a.lost_reason] += 1
    lost_reasons = sorted(
        [{"code": k, "label": LOST_REASON_LABELS.get(k, k), "count": v}
         for k, v in reason_counts.items()],
        key=lambda x: -x["count"],
    )

    return {
        "total_retrospectives": len(retros),
        "average_satisfaction": avg_score,
        "action_closure_rate": action_closure_rate,
        "renewal_rate_proxy": renewal_rate,
        "true_renewal_rate": true_renewal_rate,
        "renewed_project_count": int(renewed_count),
        "top_clients_by_project_count": top_clients,
        # Renewal funnel
        "renewal_attempts_total": len(attempts),
        "renewal_won_count": won_count,
        "renewal_lost_count": lost_count,
        "renewal_pending_count": pending_count,
        "renewal_win_rate": round(win_rate, 4),
        "renewal_lost_reasons": lost_reasons,
        "_renewal_note": "renewal_rate_proxy = ≥2 项目客户/总客户；true_renewal_rate = 显式标记/总项目；win_rate = 赢/(赢+输)",
    }


# ── helper ──────────────────────────────────────────────────────────

def _count_by(items: list[dict], key: str) -> list[dict]:
    cnt: dict[str, int] = defaultdict(int)
    for it in items:
        cnt[it.get(key, "unknown")] += 1
    return [{"label": k, "count": v} for k, v in cnt.items()]
