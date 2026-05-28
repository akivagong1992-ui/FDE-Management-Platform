from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


EXPENSE_STATUS_PATTERN = "^(pending|approved|rejected|paid)$"


class ExpenseRequestBase(BaseModel):
    project_id: int
    supplier_id: int | None = None
    engineer_id: int | None = None
    vendor_id: int | None = None  # engineer 自提时必填；vendor 自提时从 JWT 自动绑定
    expense_type: str  # code from DataDict(category=expense_type)
    title: str
    amount: Decimal = Field(gt=0)
    currency: str = "HKD"
    expense_date: date | None = None
    description: str | None = None


class ExpenseRequestCreate(ExpenseRequestBase):
    pass


class ExpenseRequestUpdate(BaseModel):
    project_id: int | None = None
    supplier_id: int | None = None
    engineer_id: int | None = None
    expense_type: str | None = None
    title: str | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    expense_date: date | None = None
    description: str | None = None


class ApprovalAction(BaseModel):
    approval_note: str | None = None


class ExpenseRequestOut(ExpenseRequestBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_name: str | None = None
    supplier_name: str | None = None
    vendor_name: str | None = None
    engineer_name: str | None = None  # resolved on output
    expense_type_label: str | None = None  # resolved from DataDict on output
    status: str
    approval_stage: str  # 'vendor' | 'lead'
    requested_by_user_id: int | None = None
    vendor_approved_by_user_id: int | None = None
    vendor_approved_at: datetime | None = None
    vendor_approval_note: str | None = None
    approved_by_user_id: int | None = None
    approved_at: datetime | None = None
    approval_note: str | None = None
    paid_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
