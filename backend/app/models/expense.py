from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# Status：流程终态/支付态。审批进展用 approval_stage 表达。
EXPENSE_STATUS_PENDING = "pending"
EXPENSE_STATUS_APPROVED = "approved"
EXPENSE_STATUS_REJECTED = "rejected"
EXPENSE_STATUS_PAID = "paid"

# Approval stage：表示当前等待哪一段审批，或终态时最后停在哪一段
APPROVAL_STAGE_VENDOR = "vendor"  # engineer 自提，等所选 vendor 批
APPROVAL_STAGE_LEAD = "lead"      # vendor 已批 / vendor 自提；等 lead/finance 批

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
    # 用户 2026-05-25 加入：vendor 用 VSF 钱付给工程师/劳务公司的部分，
    # 是 vendor 端最大开销项；进入团队真实利润公式：team_margin = VSF − Σ 全部支出
    ("outsource_engineer", "外包工程师支出"),
]


class ExpenseRequest(Base):
    """外部支出申请 — 5 类支出统一抽象（README §3 维度 4）。每笔必须挂项目以归集成本。"""

    __tablename__ = "expense_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    # 用户 2026-05-25 加入：vendor 角色提交时填的发起方公司
    # admin 看全部；vendor 用户列表时 filter where vendor_id == current_user.vendor_id
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"), index=True)
    # 受益工程师：vendor 替工程师录入差旅/培训等垫付时填，项目层级支出可空
    engineer_id: Mapped[int | None] = mapped_column(ForeignKey("engineers.id"), index=True)

    # Type code from DataDict(category=expense_type)
    expense_type: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(8), default="HKD")
    expense_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)

    # Workflow
    status: Mapped[str] = mapped_column(String(16), default=EXPENSE_STATUS_PENDING, index=True)
    approval_stage: Mapped[str] = mapped_column(String(16), default=APPROVAL_STAGE_LEAD, index=True)
    requested_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    # vendor 阶段批准记录（engineer 自提时使用；vendor 自提时跳过）
    vendor_approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    vendor_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    vendor_approval_note: Mapped[str | None] = mapped_column(Text)
    # lead 阶段批准记录（也复用为拒绝时的"最后操作者"）
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
    engineer: Mapped["Engineer | None"] = relationship(lazy="selectin")  # noqa: F821
