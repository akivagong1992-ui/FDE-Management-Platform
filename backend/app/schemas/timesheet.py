from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_SLOTS = {"morning", "afternoon", "evening"}


class TimesheetBase(BaseModel):
    engineer_id: int
    project_id: int
    assignment_id: int | None = None
    work_date: date
    has_morning: bool = False
    has_afternoon: bool = False
    has_evening: bool = False
    description: str | None = None


class TimesheetCreate(TimesheetBase):
    """单天创建：直接给某天 + 三个时段选择。"""

    @field_validator("has_evening")
    @classmethod
    def _at_least_one_slot(cls, v, info):
        data = info.data
        if not (data.get("has_morning") or data.get("has_afternoon") or v):
            raise ValueError("请至少选择一个时段（上午 / 下午 / 晚上）")
        return v


class TimesheetRangeCreate(BaseModel):
    """跨日批量：给定起止日期 + 时段，服务端逐日展开。"""

    engineer_id: int
    project_id: int
    assignment_id: int | None = None
    start_date: date
    end_date: date
    slots: list[str] = Field(min_length=1)
    description: str | None = None

    @field_validator("slots")
    @classmethod
    def _check_slots(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("请至少选择一个时段")
        bad = [s for s in v if s not in VALID_SLOTS]
        if bad:
            raise ValueError(f"非法时段: {bad}（合法: morning / afternoon / evening）")
        return list(dict.fromkeys(v))  # dedupe

    @field_validator("end_date")
    @classmethod
    def _check_range(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("截止日期不能早于起始日期")
        return v


class TimesheetUpdate(BaseModel):
    has_morning: bool | None = None
    has_afternoon: bool | None = None
    has_evening: bool | None = None
    is_workday: bool | None = None
    description: str | None = None


class TimesheetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    engineer_id: int
    engineer_name: str | None = None
    project_id: int
    project_name: str | None = None
    assignment_id: int | None = None
    work_date: date
    has_morning: bool
    has_afternoon: bool
    has_evening: bool
    is_workday: bool
    natural_days: Decimal
    weighted_days: Decimal
    description: str | None = None
    approval_status: str  # pending / approved / rejected
    reject_reason: str | None = None
    reviewed_at: datetime | None = None
    submitted_by_user_id: int | None = None
    is_approved: bool  # 旧字段兼容
    created_at: datetime


class TimesheetReject(BaseModel):
    reason: str = Field(min_length=1)


class TimesheetBulkCreate(BaseModel):
    items: list[TimesheetCreate]


class ImportRowError(BaseModel):
    row: int
    message: str


class ImportResult(BaseModel):
    created: int
    skipped: int
    errors: list[ImportRowError] = []


class TimesheetRangeResult(BaseModel):
    created: list[TimesheetOut]
    skipped: list[ImportRowError]
    total_natural_days: Decimal
    total_weighted_days: Decimal
