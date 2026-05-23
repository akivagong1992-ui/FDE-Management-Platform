from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


VSF_TYPE_PATTERN = "^(monthly_per_engineer|project_milestone|other)$"
VSF_STATUS_PATTERN = "^(draft|billed|paid)$"


class VendorServiceFeeBase(BaseModel):
    vendor_id: int
    engineer_id: int | None = None
    project_id: int | None = None
    fee_type: str = Field(default="monthly_per_engineer", pattern=VSF_TYPE_PATTERN)
    period_start: date
    period_end: date
    amount: Decimal = Field(gt=0)
    currency: str = "HKD"
    invoice_no: str | None = None
    description: str | None = None
    status: str = Field(default="draft", pattern=VSF_STATUS_PATTERN)


class VendorServiceFeeCreate(VendorServiceFeeBase):
    pass


class VendorServiceFeeUpdate(BaseModel):
    fee_type: str | None = Field(default=None, pattern=VSF_TYPE_PATTERN)
    period_start: date | None = None
    period_end: date | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    invoice_no: str | None = None
    description: str | None = None
    status: str | None = Field(default=None, pattern=VSF_STATUS_PATTERN)


class VendorServiceFeeOut(VendorServiceFeeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vendor_name: str | None = None
    engineer_name: str | None = None
    project_name: str | None = None
    paid_at: datetime | None = None
    created_at: datetime
