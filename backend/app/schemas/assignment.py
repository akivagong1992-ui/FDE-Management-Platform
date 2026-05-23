from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


ASSIGNMENT_STATUS_PATTERN = "^(planned|in_progress|ended|cancelled)$"


class AssignmentBase(BaseModel):
    engineer_id: int
    project_id: int
    role: str | None = None
    allocation_ratio: int = Field(default=100, ge=0, le=100)
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    status: str = Field(default="planned", pattern=ASSIGNMENT_STATUS_PATTERN)
    notes: str | None = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    role: str | None = None
    allocation_ratio: int | None = Field(default=None, ge=0, le=100)
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    status: str | None = Field(default=None, pattern=ASSIGNMENT_STATUS_PATTERN)
    notes: str | None = None


class AssignmentOut(AssignmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    engineer_name: str | None = None
    project_name: str | None = None
    project_code: str | None = None
    created_at: datetime
