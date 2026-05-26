"""Phase 2b · R14 — assert /api/cockpit/* responses NEVER leak A/B-tier numbers.

The compliance constraint (README §1.5): the cockpit feeds leadership and CANNOT
expose the team's actual revenue, real cost, or margin. Only the C-tier number
(savings + value_created) may surface there.
"""

import re

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

COCKPIT_HEADERS = {"X-Cockpit-Token": settings.COCKPIT_TOKEN}

# Field names that imply admin-grade A/B disclosure if they ever appear in a
# cockpit response payload. Match-case insensitive against any string in the
# JSON tree.
FORBIDDEN_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bteam_margin\b",
        r"\btotal_revenue\b",
        r"\btotal_external_expenses\b",
        r"\btotal_vendor_service_fees\b",
        r"\bvendor_fees\b",
        r"\breal_cost\b",
        r"\bmonthly_real_cost\b",
        r"\bmonthly_cost_to_telecom\b",
        # B-tier per-project / per-sales / per-client margin fields
        r"\bsales_person_id\b.*\bmargin\b",
        r"\bneed_party_id\b.*\bmargin\b",
        # 客户付款总额 + FDE 利润率提升相关字段，揭露后可反推 vendor markup
        r"\bgross_amount\b",
        r"\bgross_revenue\b",
        r"\btotal_gross_revenue\b",
        r"\boutsource_margin\b",
        r"\bfde_margin\b",
        r"\bmargin_lift\b",
        r"\bextra_profit\b",
    ]
]


def _walk_for_forbidden(node) -> list[str]:
    """Recursively walk a JSON-ish tree, collecting any string key/value matching a forbidden pattern."""
    hits: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            for pat in FORBIDDEN_PATTERNS:
                if pat.search(str(k)):
                    hits.append(f"key:{k}")
            hits.extend(_walk_for_forbidden(v))
    elif isinstance(node, list):
        for item in node:
            hits.extend(_walk_for_forbidden(item))
    elif isinstance(node, str):
        for pat in FORBIDDEN_PATTERNS:
            if pat.search(node):
                hits.append(f"value:{node[:60]}")
    return hits


def test_cockpit_overview_isolation() -> None:
    with TestClient(app) as c:
        r = c.get("/api/cockpit/overview", headers=COCKPIT_HEADERS)
        assert r.status_code == 200
        hits = _walk_for_forbidden(r.json())
        assert not hits, f"Cockpit /overview leaks A/B-tier fields: {hits}"


def test_cockpit_knowledge_stats_isolation() -> None:
    with TestClient(app) as c:
        r = c.get("/api/cockpit/knowledge-stats", headers=COCKPIT_HEADERS)
        assert r.status_code == 200
        body = r.json()
        assert "total_assets" in body
        assert "by_category" in body
        hits = _walk_for_forbidden(body)
        assert not hits, f"Cockpit /knowledge-stats leaks A/B-tier fields: {hits}"


def test_cockpit_savings_and_value_isolation() -> None:
    with TestClient(app) as c:
        r = c.get("/api/cockpit/savings-and-value", headers=COCKPIT_HEADERS)
        assert r.status_code == 200
        body = r.json()
        # C-tier surface must contain savings & value_created
        assert "savings_from_revenue_projects" in body
        assert "value_created_from_no_revenue_projects" in body
        assert "total_c_view" in body
        # And NOT contain A/B-tier surface
        hits = _walk_for_forbidden(body)
        assert not hits, f"Cockpit /savings-and-value leaks A/B-tier fields: {hits}"


def test_cockpit_margin_lift_pct_isolation() -> None:
    """D 限定版：仅 3 个百分率 + 项目数，绝不暴露任何绝对金额。"""
    with TestClient(app) as c:
        r = c.get("/api/cockpit/margin-lift-pct", headers=COCKPIT_HEADERS)
        assert r.status_code == 200
        body = r.json()
        # 必含的 3 个百分率
        assert "outsource_margin_pct" in body
        assert "fde_margin_pct" in body
        assert "margin_lift_pct" in body
        # 绝对金额字段绝不可出现
        for k in (
            "total_gross_revenue", "total_team_revenue", "total_outsource_benchmark",
            "total_actual_cost", "total_non_service_expense",
            "outsource_margin", "fde_margin", "extra_profit",
        ):
            assert k not in body, f"D 限定版泄露绝对金额字段: {k}"
        # FORBIDDEN_PATTERNS 全量隔离
        hits = _walk_for_forbidden(body)
        assert not hits, f"Cockpit /margin-lift-pct leaks A/B-tier fields: {hits}"


# ── Phase 3 bulk · 5 new aggregation endpoints ─────────────────────────

def _assert_isolation(client: TestClient, path: str) -> None:
    r = client.get(path, headers=COCKPIT_HEADERS)
    assert r.status_code == 200, f"{path} → {r.status_code}: {r.text[:200]}"
    hits = _walk_for_forbidden(r.json())
    assert not hits, f"{path} leaks A/B-tier fields: {hits}"


def test_cockpit_aggregations_isolation() -> None:
    """所有 cockpit aggregation 端点不得泄露 A/B 数字。
    relationship-stats 已撤掉（Tab 8 整个被移除），故不在列表内。"""
    paths = [
        "/api/cockpit/project-board",
        "/api/cockpit/profit-compare",
        "/api/cockpit/engineer-stats",
        "/api/cockpit/efficiency-stats",
        "/api/cockpit/capability-stats",
        "/api/cockpit/growth-trend",
    ]
    with TestClient(app) as c:
        for p in paths:
            _assert_isolation(c, p)
