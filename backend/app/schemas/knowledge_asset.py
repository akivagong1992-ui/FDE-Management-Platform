from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


CONFIDENTIALITY_PATTERN = "^(public|internal|confidential)$"


class KnowledgeAssetBase(BaseModel):
    project_id: int | None = None
    category: str
    title: str
    summary: str | None = None
    content: str | None = None
    external_url: str | None = None
    file_path: str | None = None
    tags: str | None = None  # comma-separated
    confidentiality: str = Field(default="internal", pattern=CONFIDENTIALITY_PATTERN)


class KnowledgeAssetCreate(KnowledgeAssetBase):
    pass


class KnowledgeAssetUpdate(BaseModel):
    project_id: int | None = None
    category: str | None = None
    title: str | None = None
    summary: str | None = None
    content: str | None = None
    external_url: str | None = None
    file_path: str | None = None
    tags: str | None = None
    confidentiality: str | None = Field(default=None, pattern=CONFIDENTIALITY_PATTERN)


class KnowledgeAssetOut(KnowledgeAssetBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_name: str | None = None
    category_label: str | None = None  # resolved from DataDict
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class KnowledgeStats(BaseModel):
    """Cockpit Tab 6 — 知识资产统计（口径 C 范畴：成果展示，不涉及金额）。"""

    total: int
    by_category: list[dict]
    recent_count_30d: int
    project_coverage: int  # 有产出知识资产的项目数