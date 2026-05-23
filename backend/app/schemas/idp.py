from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


IDP_STATUS_PATTERN = "^(draft|in_progress|completed|cancelled)$"


class IDPBase(BaseModel):
    engineer_id: int
    title: str
    target_skills: str | None = None
    target_certs: str | None = None
    plan_actions: str | None = None
    due_date: date | None = None
    status: str = Field(default="draft", pattern=IDP_STATUS_PATTERN)
    mentor_user_id: int | None = None


class IDPCreate(IDPBase):
    pass


class IDPUpdate(BaseModel):
    title: str | None = None
    target_skills: str | None = None
    target_certs: str | None = None
    plan_actions: str | None = None
    due_date: date | None = None
    status: str | None = Field(default=None, pattern=IDP_STATUS_PATTERN)
    mentor_user_id: int | None = None


class IDPOut(IDPBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    engineer_name: str | None = None
    created_at: datetime
    updated_at: datetime
