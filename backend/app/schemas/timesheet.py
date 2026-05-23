from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


HALF = Decimal("0.5")


def _is_half_step(value: Decimal) -> Decimal:
    """工时以 0.5 人天为最小步进（0.5/1.0/1.5/...）。"""
    if value <= 0:
        raise ValueError("人天必须 > 0")
    if value > 3:
        raise ValueError("单日人天 ≤ 3（含加班场景）；如需更高请与负责人对齐")
    # value must be a multiple of 0.5
    if (value / HALF) % 1 != 0:
        raise ValueError("人天必须是 0.5 的自然倍数（0.5 / 1.0 / 1.5 / ...）")
    return value


class TimesheetBase(BaseModel):
    engineer_id: int
    project_id: int
    assignment_id: int | None = None
    work_date: date
    person_days: Decimal
    description: str | None = None

    @field_validator("person_days")
    @classmethod
    def _check_person_days(cls, v: Decimal) -> Decimal:
        return _is_half_step(v)


class TimesheetCreate(TimesheetBase):
    pass


class TimesheetUpdate(BaseModel):
    person_days: Decimal | None = None
    description: str | None = None

    @field_validator("person_days")
    @classmethod
    def _check_person_days(cls, v: Decimal | None) -> Decimal | None:
        if v is None:
            return None
        return _is_half_step(v)


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
