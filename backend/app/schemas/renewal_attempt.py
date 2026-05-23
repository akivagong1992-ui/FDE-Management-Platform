from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


OUTCOME_PATTERN = "^(pending|won|lost)$"
LOST_REASON_PATTERN = "^(lost_to_outsource|price|quality|no_budget|internal_hire|other)$"


class RenewalAttemptBase(BaseModel):
    previous_project_id: int
    attempt_date: date
    outcome: str = Field(default="pending", pattern=OUTCOME_PATTERN)
    won_project_id: int | None = None
    lost_reason: str | None = Field(default=None, pattern=f"({LOST_REASON_PATTERN})?")
    lost_reason_note: str | None = None
    notes: str | None = None


class RenewalAttemptCreate(RenewalAttemptBase):
    pass


class RenewalAttemptUpdate(BaseModel):
    attempt_date: date | None = None
    outcome: str | None = Field(default=None, pattern=OUTCOME_PATTERN)
    won_project_id: int | None = None
    lost_reason: str | None = None
    lost_reason_note: str | None = None
    notes: str | None = None


class RenewalAttemptOut(RenewalAttemptBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    previous_project_name: str | None = None
    won_project_name: str | None = None
    created_at: datetime
    updated_at: datetime
