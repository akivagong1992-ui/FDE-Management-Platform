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
