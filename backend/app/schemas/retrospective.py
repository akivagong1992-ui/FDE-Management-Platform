from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class RetrospectiveBase(BaseModel):
    project_id: int
    satisfaction_score: int = Field(ge=1, le=5)
    what_went_well: str | None = None
    what_to_improve: str | None = None
    action_items: str | None = None
    next_review_date: date | None = None
    is_closed: bool = False


class RetrospectiveCreate(RetrospectiveBase):
    pass


class RetrospectiveUpdate(BaseModel):
    satisfaction_score: int | None = Field(default=None, ge=1, le=5)
    what_went_well: str | None = None
    what_to_improve: str | None = None
    action_items: str | None = None
    next_review_date: date | None = None
    is_closed: bool | None = None


class RetrospectiveOut(RetrospectiveBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_name: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime
