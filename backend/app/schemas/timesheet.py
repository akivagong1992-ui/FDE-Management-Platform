from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TimesheetBase(BaseModel):
    engineer_id: int
    project_id: int
    assignment_id: int | None = None
    work_date: date
    hours: Decimal = Field(gt=0, le=24)
    description: str | None = None


class TimesheetCreate(TimesheetBase):
    pass


class TimesheetUpdate(BaseModel):
    hours: Decimal | None = Field(default=None, gt=0, le=24)
    description: str | None = None


class TimesheetOut(TimesheetBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    engineer_name: str | None = None
    project_name: str | None = None
    is_approved: bool
    created_at: datetime


class TimesheetBulkCreate(BaseModel):
    items: list[TimesheetCreate]


class ImportRowError(BaseModel):
    row: int
    message: str


class ImportResult(BaseModel):
    created: int
    skipped: int
    errors: list[ImportRowError] = []
