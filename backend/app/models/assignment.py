from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


ASSIGNMENT_STATUS_PLANNED = "planned"
ASSIGNMENT_STATUS_IN_PROGRESS = "in_progress"
ASSIGNMENT_STATUS_ENDED = "ended"
ASSIGNMENT_STATUS_CANCELLED = "cancelled"


class Assignment(Base):
    """派单 — 工程师 × 项目 × 时段 × 角色 × 工时占比。"""

    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineers.id"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)

    role: Mapped[str | None] = mapped_column(String(64))  # e.g. 开发/测试/PM/架构师
    allocation_ratio: Mapped[int] = mapped_column(Integer, default=100)  # 0-100 (%)
    planned_start_date: Mapped[date | None] = mapped_column(Date)
    planned_end_date: Mapped[date | None] = mapped_column(Date)
    actual_start_date: Mapped[date | None] = mapped_column(Date)
    actual_end_date: Mapped[date | None] = mapped_column(Date)

    status: Mapped[str] = mapped_column(String(16), default=ASSIGNMENT_STATUS_PLANNED, index=True)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    engineer: Mapped["Engineer"] = relationship(lazy="selectin")  # noqa: F821
    project: Mapped["Project"] = relationship(lazy="selectin")  # noqa: F821
