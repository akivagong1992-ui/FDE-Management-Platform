from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TrainingBase(BaseModel):
    engineer_id: int
    course_name: str
    provider: str | None = None
    category: str | None = Field(default=None, pattern="^(内训|外训|在线|会议|其他)?$")
    training_date: date
    hours: Decimal = Field(gt=0, le=200)
    cost: Decimal | None = None
    passed: bool = True
    notes: str | None = None


class TrainingCreate(TrainingBase):
    pass


class TrainingUpdate(BaseModel):
    course_name: str | None = None
    provider: str | None = None
    category: str | None = None
    training_date: date | None = None
    hours: Decimal | None = Field(default=None, gt=0, le=200)
    cost: Decimal | None = None
    passed: bool | None = None
    notes: str | None = None


class TrainingOut(TrainingBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    engineer_name: str | None = None
    created_at: datetime
