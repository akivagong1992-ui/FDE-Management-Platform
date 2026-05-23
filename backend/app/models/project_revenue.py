from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


REVENUE_STATUS_PENDING = "pending"        # 待回款
REVENUE_STATUS_RECEIVED = "received"      # 已到账
REVENUE_STATUS_WRITTEN_OFF = "written_off"  # 坏账核销


class ProjectRevenue(Base):
    """项目收入登记（仅 revenue 类项目）— 一项目可有多笔收入（分期到账）。"""

    __tablename__ = "project_revenues"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)

    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(8), default="HKD")
    recognized_date: Mapped[date] = mapped_column(Date, index=True)
    invoice_no: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(16), default=REVENUE_STATUS_PENDING)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped["Project"] = relationship(lazy="selectin")  # noqa: F821
