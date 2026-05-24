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

# Outsource benchmark basis (R6) — 节省金额公式背后的依据
BENCHMARK_BASIS_HISTORICAL = "historical_avg"      # 同类历史项目均价
BENCHMARK_BASIS_INDUSTRY = "industry_benchmark"    # 行业基准 / 公开报告
BENCHMARK_BASIS_VENDOR_QUOTE = "vendor_quote"      # 外包供应商真实报价单
BENCHMARK_BASIS_MANUAL = "manual_estimate"         # 经验估算（最弱）


# ─── Enums ─────────────────────────────────────────────────────────────

# Project kind (README §1.6)
PROJECT_KIND_REVENUE = "revenue"          # 有收入项目
PROJECT_KIND_NO_REVENUE = "no_revenue"    # 无收入项目（必须有 value_created_basis）

# Status machine — 执行生命周期
PROJECT_STATUS_DRAFTING = "drafting"      # 立项
PROJECT_STATUS_IN_PROGRESS = "in_progress"  # 进行中
PROJECT_STATUS_ACCEPTING = "accepting"    # 验收
PROJECT_STATUS_CLOSING = "closing"        # 收尾
PROJECT_STATUS_ARCHIVED = "archived"      # 归档
PROJECT_STATUS_CANCELLED = "cancelled"    # 跑单 / 中途取消（保留向后兼容；新数据用 bid_outcome=escaped）

# Bid outcome — 投标结果（与 status 正交：一个项目可同时 bid_outcome=won + status=in_progress）
PROJECT_BID_OUTCOME_PENDING = "pending"   # 投标中 / 未定（默认）
PROJECT_BID_OUTCOME_WON = "won"           # 已中标 → C-tier savings 立即计入（默认团队一定拿到 team revenue）
PROJECT_BID_OUTCOME_LOST = "lost"         # 已丢标 → 不计入任何 cockpit 指标
PROJECT_BID_OUTCOME_ESCAPED = "escaped"   # 中标后跑单（客户违约） → 不计入

# value_created_basis (only for no_revenue)
VALUE_BASIS_OUTSOURCE_EQUIV = "outsource_equiv"        # 等同外包服务所抵消的成本（默认）
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
    # 对接工程师：派工到工程师团队的人（区别于 pm_user — pm 是项目经理 user，对接工程师是 engineers 表里的派工人员）
    contact_engineer_id: Mapped[int | None] = mapped_column(ForeignKey("engineers.id"))

    # 分类（README §1.6） — 影响 C 口径计算
    kind: Mapped[str] = mapped_column(String(16), default=PROJECT_KIND_REVENUE, index=True)

    # 价值估算 — 两种项目都填，C 口径用
    outsource_benchmark_amount: Mapped[float | None] = mapped_column(Numeric(14, 2))
    # R6: 外包估算的依据，影响 C 口径数字的可信度（仅元数据，不影响计算）
    benchmark_basis: Mapped[str | None] = mapped_column(String(32))     # historical_avg / industry_benchmark / vendor_quote / manual_estimate
    benchmark_basis_note: Mapped[str | None] = mapped_column(Text)      # 依据说明（如参考的历史项目编号、行业报告链接）
    # 若项目为 no_revenue：value_created 默认 = outsource_benchmark_amount
    # 仅当 no_revenue 时启用以下两个字段
    value_created_basis: Mapped[str | None] = mapped_column(String(32))
    value_created_note: Mapped[str | None] = mapped_column(Text)

    # 状态机
    status: Mapped[str] = mapped_column(String(16), default=PROJECT_STATUS_DRAFTING, index=True)
    # 投标结果（决定是否计入驾驶舱 C-tier savings）
    bid_outcome: Mapped[str] = mapped_column(
        String(16), default=PROJECT_BID_OUTCOME_PENDING, index=True
    )

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
    summary: Mapped[str | None] = mapped_column(Text)        # 一句话项目摘要（/efficiency 表显示）
    description: Mapped[str | None] = mapped_column(Text)    # 详细说明
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    need_party: Mapped["NeedParty"] = relationship(lazy="selectin")  # noqa: F821
    sales_person: Mapped["SalesPerson"] = relationship(lazy="selectin")  # noqa: F821


class ProjectComment(Base):
    """项目评论流 — admin/lead/pm 与 engineer 之间的互动动作（催办、回复、备注）。"""

    __tablename__ = "project_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    author_role: Mapped[str] = mapped_column(String(16))   # 冗余存当时的 role 便于审计
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


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
