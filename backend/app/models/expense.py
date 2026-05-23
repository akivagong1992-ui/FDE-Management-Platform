from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# Phase 2a uses simplified single-level approval:
EXPENSE_STATUS_PENDING = "pending"
EXPENSE_STATUS_APPROVED = "approved"
EXPENSE_STATUS_REJECTED = "rejected"
EXPENSE_STATUS_PAID = "paid"

# Seeded into DataDict on startup (category="expense_type"):
# 新启动会增量补码，不会覆盖已有；training 是 Phase 3-next 新增（培训学费走外部支出）
EXPENSE_TYPE_DEFAULTS = [
    ("material", "耗材"),
    ("subcontract", "对外分包高级服务"),
    ("temp_labor", "临时人力补充"),
    ("license", "第三方平台 / 许可证"),
    ("travel", "差旅 / 外勤"),
    ("training", "外部培训费"),
    ("other", "其他（不在以上分类的开销）"),
]


class ExpenseRequest(Base):
    """外部支出申请 — 5 类支出统一抽象（README §3 维度 4）。每笔必须挂项目以归集成本。"""

    __tablename__ = "expense_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))

    # Type code from DataDict(category=expense_type)
    expense_type: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(8), default="HKD")
    expense_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)

    # Workflow
    status: Mapped[str] = mapped_column(String(16), default=EXPENSE_STATUS_PENDING, index=True)
    requested_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approval_note: Mapped[str | None] = mapped_column(Text)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped["Project"] = relationship(lazy="selectin")  # noqa: F821
    supplier: Mapped["Supplier | None"] = relationship(lazy="selectin")  # noqa: F821
