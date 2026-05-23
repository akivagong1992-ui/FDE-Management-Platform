from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


IDP_STATUS_DRAFT = "draft"
IDP_STATUS_IN_PROGRESS = "in_progress"
IDP_STATUS_COMPLETED = "completed"
IDP_STATUS_CANCELLED = "cancelled"


class IDP(Base):
    """工程师个人发展计划 IDP（PLAN §4.8）— 目标技能 + 截止 + 状态。"""

    __tablename__ = "idps"

    id: Mapped[int] = mapped_column(primary_key=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineers.id"), index=True)

    title: Mapped[str] = mapped_column(String(128))         # 比如 "L4 → L5 路径"
    target_skills: Mapped[str | None] = mapped_column(Text)  # 目标技能（逗号分隔）
    target_certs: Mapped[str | None] = mapped_column(Text)   # 目标证书
    plan_actions: Mapped[str | None] = mapped_column(Text)   # 行动项（一行一条）
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), default=IDP_STATUS_DRAFT, index=True)

    mentor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    engineer: Mapped["Engineer"] = relationship(lazy="selectin")  # noqa: F821
