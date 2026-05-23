from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


PROJECT_KIND_PATTERN = "^(revenue|no_revenue)$"
PROJECT_STATUS_PATTERN = "^(drafting|in_progress|accepting|closing|archived)$"
VALUE_BASIS_PATTERN = (
    "^(outsource_equiv|replace_audit_fee|avoid_penalty|save_hours|strategic_reserve|other)$"
)
TRANSFER_REASON_PATTERN = "^(resignation|role_change|other)$"


class ProjectBase(BaseModel):
    code: str | None = None
    name: str
    need_party_id: int
    sales_person_id: int
    pm_user_id: int | None = None
    kind: str = Field(default="revenue", pattern=PROJECT_KIND_PATTERN)
    outsource_benchmark_amount: Decimal | None = None
    value_created_basis: str | None = Field(default=None, pattern=f"({VALUE_BASIS_PATTERN})?")
    value_created_note: str | None = None
    status: str = Field(default="drafting", pattern=PROJECT_STATUS_PATTERN)
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    description: str | None = None

    # Phase 3-next-ii
    district: str | None = None  # HK_ISLAND/KOWLOON/NT_EAST/NT_WEST/OUTLYING
    rework_count: int = 0
    change_count: int = 0
    renewal_of_project_id: int | None = None

    # Phase 3-next-iii (R6 — outsource benchmark credibility)
    benchmark_basis: str | None = Field(
        default=None,
        pattern="^(historical_avg|industry_benchmark|vendor_quote|manual_estimate)?$",
    )
    benchmark_basis_note: str | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    need_party_id: int | None = None
    # sales_person_id is NOT directly updatable — use POST /transfer-sales instead
    pm_user_id: int | None = None
    kind: str | None = Field(default=None, pattern=PROJECT_KIND_PATTERN)  # change requires lead role
    outsource_benchmark_amount: Decimal | None = None
    value_created_basis: str | None = None
    value_created_note: str | None = None
    status: str | None = Field(default=None, pattern=PROJECT_STATUS_PATTERN)
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    description: str | None = None
    district: str | None = None
    rework_count: int | None = None
    change_count: int | None = None
    renewal_of_project_id: int | None = None
    benchmark_basis: str | None = None
    benchmark_basis_note: str | None = None


class ProjectOut(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    # Denormalized for UI convenience
    need_party_name: str | None = None
    sales_person_name: str | None = None
    sales_person_active: bool | None = None
    # Computed: for no_revenue projects, value_created = outsource_benchmark_amount (R13 auto-calc)
    value_created_computed: Decimal | None = None
    created_at: datetime
    updated_at: datetime


class TransferSalesRequest(BaseModel):
    to_sales_person_id: int
    reason: str = Field(pattern=TRANSFER_REASON_PATTERN)
    reason_note: str | None = None


class SalesTransferLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    from_sales_person_id: int
    to_sales_person_id: int
    reason: str
    reason_note: str | None = None
    operator_user_id: int | None = None
    created_at: datetime
