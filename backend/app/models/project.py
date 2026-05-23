from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# Hong Kong administrative regions (macro)
HK_DISTRICTS = [
    ("HK_ISLAND", "港岛"),
    ("KOWLOON", "九龙"),
    ("NT_EAST", "新界东"),
    ("NT_WEST", "新界西"),
    ("OUTLYING", "离岛"),
]


# ─── Enums ─────────────────────────────────────────────────────────────

# Project kind (README §1.6)
PROJECT_KIND_REVENUE = "revenue"          # 有收入项目
PROJECT_KIND_NO_REVENUE = "no_revenue"    # 无收入项目（必须有 value_created_basis）

# Status machine
PROJECT_STATUS_DRAFTING = "drafting"      # 立项
PROJECT_STATUS_IN_PROGRESS = "in_progress"  # 进行中
PROJECT_STATUS_ACCEPTING = "accepting"    # 验收
PROJECT_STATUS_CLOSING = "closing"        # 收尾
PROJECT_STATUS_ARCHIVED = "archived"      # 归档

# value_created_basis (only for no_revenue)
VALUE_BASIS_OUTSOURCE_EQUIV = "outsource_equiv"        # 等同外包成本（默认）
VALUE_BASIS_REPLACE_AUDIT = "replace_audit_fee"        # 替代外部审计 / 咨询费
VALUE_BASIS_AVOID_PENALTY = "avoid_penalty"            # 避免合规罚款
VALUE_BASIS_SAVE_HOURS = "save_hours"                  # 节省工时折算
VALUE_BASIS_STRATEGIC = "strategic_reserve"            # 战略储备
VALUE_BASIS_OTHER = "other"                            # 其他（必填备注）

# SalesTransferLog reason
TRANSFER_REASON_RESIGNATION = "resignation"
TRANSFER_REASON_ROLE_CHANGE = "role_change"
TRANSFER_REASON_OTHER = "other"


class Project(Base):
    """项目 — 立项时挂销售人员 + 需求方，类型分有/无收入（影响 C 口径）."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str | None] = mapped_column(String(32), unique=True, index=True)  # 项目编号 (可选自定义)
    name: Mapped[str] = mapped_column(String(128), index=True)

    # 关联
    need_party_id: Mapped[int] = mapped_column(ForeignKey("need_parties.id"), index=True)
    sales_person_id: Mapped[int] = mapped_column(ForeignKey("sales_persons.id"), index=True)
    pm_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    # 分类（README §1.6） — 影响 C 口径计算
    kind: Mapped[str] = mapped_column(String(16), default=PROJECT_KIND_REVENUE, index=True)

    # 价值估算 — 两种项目都填，C 口径用
    outsource_benchmark_amount: Mapped[float | None] = mapped_column(Numeric(14, 2))
    # 若项目为 no_revenue：value_created 默认 = outsource_benchmark_amount
    # 仅当 no_revenue 时启用以下两个字段
    value_created_basis: Mapped[str | None] = mapped_column(String(32))
    value_created_note: Mapped[str | None] = mapped_column(Text)

    # 状态机
    status: Mapped[str] = mapped_column(String(16), default=PROJECT_STATUS_DRAFTING, index=True)

    # 时间
    planned_start_date: Mapped[date | None] = mapped_column(Date)
    planned_end_date: Mapped[date | None] = mapped_column(Date)
    actual_start_date: Mapped[date | None] = mapped_column(Date)
    actual_end_date: Mapped[date | None] = mapped_column(Date)

    # 地区 + 效率 + 续单（Phase 3-next-ii）
    district: Mapped[str | None] = mapped_column(String(16), index=True)  # HK_ISLAND/KOWLOON/...
    rework_count: Mapped[int] = mapped_column(Integer, default=0)        # 返工次数
    change_count: Mapped[int] = mapped_column(Integer, default=0)        # 变更单次数
    renewal_of_project_id: Mapped[int | None] = mapped_column(            # 续单：上一单 FK
        ForeignKey("projects.id"), index=True
    )

    # 元
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    need_party: Mapped["NeedParty"] = relationship(lazy="selectin")  # noqa: F821
    sales_person: Mapped["SalesPerson"] = relationship(lazy="selectin")  # noqa: F821


class SalesTransferLog(Base):
    """转移销售审计日志（R15）— 项目销售归属变更时记录，用于追溯。"""

    __tablename__ = "sales_transfer_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    from_sales_person_id: Mapped[int] = mapped_column(ForeignKey("sales_persons.id"))
    to_sales_person_id: Mapped[int] = mapped_column(ForeignKey("sales_persons.id"))
    reason: Mapped[str] = mapped_column(String(32))  # resignation / role_change / other
    reason_note: Mapped[str | None] = mapped_column(Text)
    operator_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
