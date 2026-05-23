from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TrainingRecord(Base):
    """培训记录（PLAN §4.8）— 一条 = 一个工程师参加一次培训。"""

    __tablename__ = "training_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineers.id"), index=True)

    course_name: Mapped[str] = mapped_column(String(128))
    provider: Mapped[str | None] = mapped_column(String(128))  # 培训机构 / 内训师
    category: Mapped[str | None] = mapped_column(String(32))   # 内训/外训/在线/会议
    training_date: Mapped[date] = mapped_column(Date, index=True)
    hours: Mapped[float] = mapped_column(Numeric(5, 1))        # 培训学时
    cost: Mapped[float | None] = mapped_column(Numeric(12, 2)) # 仅 lead/finance 可见
    passed: Mapped[bool] = mapped_column(default=True)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    engineer: Mapped["Engineer"] = relationship(lazy="selectin")  # noqa: F821
