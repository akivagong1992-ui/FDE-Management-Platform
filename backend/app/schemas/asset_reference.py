from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AssetReferenceCreate(BaseModel):
    project_id: int
    estimated_hours_saved: Decimal | None = Field(default=None, ge=0, le=10000)
    notes: str | None = None


class AssetReferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    asset_id: int
    project_id: int
    project_name: str | None = None
    estimated_hours_saved: Decimal | None = None
    notes: str | None = None
    referenced_by_user_id: int | None = None
    referenced_at: datetime
