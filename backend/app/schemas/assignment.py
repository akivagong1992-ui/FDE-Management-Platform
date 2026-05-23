from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


ASSIGNMENT_STATUS_PATTERN = "^(planned|in_progress|ended|cancelled)$"
APPROVAL_STATUS_PATTERN = "^(pending|accepted|rejected)$"


class AssignmentBase(BaseModel):
    engineer_id: int
    project_id: int
    role: str | None = None
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    status: str = Field(default="planned", pattern=ASSIGNMENT_STATUS_PATTERN)
    notes: str | None = None


class AssignmentCreate(AssignmentBase):
    initial_message: str | None = None  # PM 创建时可附加首条说明


class AssignmentUpdate(BaseModel):
    role: str | None = None
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    actual_start_date: date | None = None
    actual_end_date: date | None = None
    status: str | None = Field(default=None, pattern=ASSIGNMENT_STATUS_PATTERN)
    notes: str | None = None


class AssignmentMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sender_user_id: int | None = None
    sender_name: str | None = None
    sender_kind: str  # system / pm / engineer
    body: str
    created_at: datetime


class AssignmentOut(AssignmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    engineer_name: str | None = None
    project_name: str | None = None
    project_code: str | None = None
    approval_status: str
    engineer_responded_at: datetime | None = None
    created_by_user_id: int | None = None
    message_count: int = 0
    created_at: datetime


class AssignmentAccept(BaseModel):
    note: str | None = None  # 接单时可选附言


class AssignmentReject(BaseModel):
    reason: str = Field(min_length=1)  # 拒单理由必填


class AssignmentReply(BaseModel):
    body: str = Field(min_length=1)
