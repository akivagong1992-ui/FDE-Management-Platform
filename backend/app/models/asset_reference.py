from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssetReference(Base):
    """知识资产被某项目引用 / 复用一次。每次引用可填"节省工时"折算 C 口径。"""

    __tablename__ = "asset_references"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_assets.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)

    estimated_hours_saved: Mapped[float | None] = mapped_column(Numeric(6, 1))  # 人时折算
    notes: Mapped[str | None] = mapped_column(Text)

    referenced_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    referenced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(lazy="selectin")  # noqa: F821
