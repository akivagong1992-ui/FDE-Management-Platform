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

    # amount = 团队入账（pass-through 到 Vendor 的部分），用于团队成本核算 + 驾驶舱降本
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    # gross_amount = 客户付款总额（销售切除前），用于公司级毛利率计算（仅 admin 可见）
    gross_amount: Mapped[float | None] = mapped_column(Numeric(14, 2))
    # non_service_expense = 非服务开销（硬件采购 / 第三方软件 / 物料等公司直付支出，占 gross 约 65-75%）
    # 公司毛利率公式：(gross − benchmark − non_service_expense) / gross
    non_service_expense: Mapped[float | None] = mapped_column(Numeric(14, 2))
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
