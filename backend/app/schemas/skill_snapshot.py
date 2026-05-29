from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SkillSnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    engineer_id: int
    engineer_name: str | None = None
    snapshot_date: date
    skill_count: int
    avg_level: Decimal
    level: int | None = None
    created_at: datetime


class SnapshotTriggerResult(BaseModel):
    snapshot_date: date
    created: int
    skipped: int  # 已存在同日快照的工程师数
