from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


VSF_TYPE_MONTHLY_PER_ENGINEER = "monthly_per_engineer"  # 按工程师月度服务费
VSF_TYPE_PROJECT_MILESTONE = "project_milestone"        # 按项目里程碑服务费
VSF_TYPE_OTHER = "other"

VSF_STATUS_DRAFT = "draft"
VSF_STATUS_BILLED = "billed"
VSF_STATUS_PAID = "paid"


class VendorServiceFee(Base):
    """付给 Vendor 的项目服务费（三层成本透视第一层 — 实际支付）。"""

    __tablename__ = "vendor_service_fees"

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    engineer_id: Mapped[int | None] = mapped_column(ForeignKey("engineers.id"))  # 可标记是给哪个工程师
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))   # 可挂项目做成本归集

    fee_type: Mapped[str] = mapped_column(String(32), default=VSF_TYPE_MONTHLY_PER_ENGINEER)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(8), default="HKD")
    invoice_no: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(16), default=VSF_STATUS_DRAFT)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vendor: Mapped["Vendor"] = relationship(lazy="selectin")  # noqa: F821
    engineer: Mapped["Engineer | None"] = relationship(lazy="selectin")  # noqa: F821
    project: Mapped["Project | None"] = relationship(lazy="selectin")  # noqa: F821
