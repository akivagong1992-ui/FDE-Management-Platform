from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProjectRevenueBase(BaseModel):
    project_id: int
    vendor_id: int  # 必填：经办 vendor（pass-through 模型下，会同步建一笔等额 VSF 镜像）
    amount: Decimal = Field(gt=0)  # 团队入账（pass-through 到 Vendor）
    gross_amount: Decimal | None = None  # 客户付款总额（销售切除前）
    non_service_expense: Decimal | None = None  # 非服务开销（硬件 / 第三方 / 物料）
    currency: str = "HKD"
    recognized_date: date
    invoice_no: str | None = None
    description: str | None = None


class ProjectRevenueCreate(ProjectRevenueBase):
    pass


class ProjectRevenueUpdate(BaseModel):
    vendor_id: int | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    gross_amount: Decimal | None = None
    non_service_expense: Decimal | None = None
    recognized_date: date | None = None
    invoice_no: str | None = None
    description: str | None = None


class ProjectRevenueOut(ProjectRevenueBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_name: str | None = None
    vendor_name: str | None = None
    created_at: datetime
