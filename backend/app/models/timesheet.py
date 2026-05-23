from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Timesheet(Base):
    """工时记录 — 工程师在某项目某天的工时。"""

    __tablename__ = "timesheets"
    __table_args__ = (
        UniqueConstraint("engineer_id", "project_id", "work_date", name="uq_ts_eng_proj_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineers.id"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    assignment_id: Mapped[int | None] = mapped_column(ForeignKey("assignments.id"))

    work_date: Mapped[date] = mapped_column(Date, index=True)
    hours: Mapped[float] = mapped_column(Numeric(5, 2))  # e.g. 8.00, max 24
    description: Mapped[str | None] = mapped_column(Text)

    is_approved: Mapped[bool] = mapped_column(default=False)
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    engineer: Mapped["Engineer"] = relationship(lazy="selectin")  # noqa: F821
    project: Mapped["Project"] = relationship(lazy="selectin")  # noqa: F821
