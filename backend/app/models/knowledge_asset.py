from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# Confidentiality levels (per README §1.6 / PLAN §4.7)
CONFIDENTIALITY_PUBLIC = "public"          # 公开：所有登录用户可见
CONFIDENTIALITY_INTERNAL = "internal"      # 内部：所有登录用户可见（默认）
CONFIDENTIALITY_CONFIDENTIAL = "confidential"  # 机密：仅 lead/admin/finance/pm 可见

# Seeded into DataDict on startup (category="asset_category"):
ASSET_CATEGORY_DEFAULTS = [
    ("design_doc", "设计文档"),
    ("tech_solution", "技术方案"),
    ("code_snippet", "代码片段 / 模板"),
    ("troubleshoot", "问题解决手册"),
    ("standard", "工艺标准 / 规范"),
    ("best_practice", "最佳实践"),
    ("other", "其他"),
]


class KnowledgeAsset(Base):
    """技术沉淀 / 知识资产 — 项目产出归档，跨项目复用（README §3 维度 6 ⭐）。"""

    __tablename__ = "knowledge_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))  # 来源项目，可空

    # Classification
    category: Mapped[str] = mapped_column(String(32), index=True)  # code from DataDict(asset_category)
    title: Mapped[str] = mapped_column(String(255), index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)               # Markdown / plain text
    external_url: Mapped[str | None] = mapped_column(String(512))   # 外链（confluence/git/...）
    file_path: Mapped[str | None] = mapped_column(String(512))      # uploads/... 相对路径

    # Tags as comma-separated string (lightweight; pg full-text 改进可 Phase 4)
    tags: Mapped[str | None] = mapped_column(String(255))

    confidentiality: Mapped[str] = mapped_column(
        String(16), default=CONFIDENTIALITY_INTERNAL, index=True
    )

    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped["Project | None"] = relationship(lazy="selectin")  # noqa: F821
