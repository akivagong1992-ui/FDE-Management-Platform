from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


REVENUE_STATUS_PATTERN = "^(pending|received|written_off)$"


class ProjectRevenueBase(BaseModel):
    project_id: int
    amount: Decimal = Field(gt=0)  # 团队入账（pass-through 到 Vendor）
    gross_amount: Decimal | None = None  # 客户付款总额（销售切除前），仅 admin 录入
    currency: str = "HKD"
    recognized_date: date
    invoice_no: str | None = None
    description: str | None = None
    status: str = Field(default="pending", pattern=REVENUE_STATUS_PATTERN)


class ProjectRevenueCreate(ProjectRevenueBase):
    pass


class ProjectRevenueUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    gross_amount: Decimal | None = None
    recognized_date: date | None = None
    invoice_no: str | None = None
    description: str | None = None
    status: str | None = Field(default=None, pattern=REVENUE_STATUS_PATTERN)


class ProjectRevenueOut(ProjectRevenueBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_name: str | None = None
    received_at: datetime | None = None
    created_at: datetime
