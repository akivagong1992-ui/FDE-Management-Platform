from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# 每个时段的「自然人天」基准 — 1 天 = 上午 0.5 + 下午 0.5 + 晚上 0.5（晚上算第三个 slot）
NATURAL_PER_SLOT = Decimal("0.5")
# 倍率：香港工作日上下午 = 1.0；工作日晚上 + 非工作日全天 = 1.5
WORKDAY_MULTIPLIER = Decimal("1.0")
OVERTIME_MULTIPLIER = Decimal("1.5")

SLOT_MORNING = "morning"
SLOT_AFTERNOON = "afternoon"
SLOT_EVENING = "evening"
ALL_SLOTS = (SLOT_MORNING, SLOT_AFTERNOON, SLOT_EVENING)


def is_hk_workday(d: date) -> bool:
    """初版口径：周一至周五 = 工作日；周末 = 非工作日。
    HK 法定假日未来可扩展为独立 holiday 表，默认空表时本函数即正确。
    """
    return d.weekday() < 5  # Mon=0..Sun=6


def compute_weighted_days(
    work_date: date, has_morning: bool, has_afternoon: bool, has_evening: bool,
    is_workday: bool | None = None,
) -> tuple[Decimal, Decimal]:
    """返回 (natural_days, weighted_days)。
    自然人天 = 0.5 × 选中时段数。
    加权人天 = 上下午（工作日 1.0×，非工作日 1.5×）+ 晚上（始终 1.5×）。
    """
    if is_workday is None:
        is_workday = is_hk_workday(work_date)
    day_mul = WORKDAY_MULTIPLIER if is_workday else OVERTIME_MULTIPLIER
    natural = Decimal("0")
    weighted = Decimal("0")
    if has_morning:
        natural += NATURAL_PER_SLOT
        weighted += NATURAL_PER_SLOT * day_mul
    if has_afternoon:
        natural += NATURAL_PER_SLOT
        weighted += NATURAL_PER_SLOT * day_mul
    if has_evening:
        natural += NATURAL_PER_SLOT
        weighted += NATURAL_PER_SLOT * OVERTIME_MULTIPLIER  # 晚上始终 1.5×
    return natural, weighted


class Timesheet(Base):
    """工时记录 — 工程师在某项目某天的时段投入，自动按香港工时规则加权。"""

    __tablename__ = "timesheets"
    __table_args__ = (
        UniqueConstraint("engineer_id", "project_id", "work_date", name="uq_ts_eng_proj_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineers.id"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    assignment_id: Mapped[int | None] = mapped_column(ForeignKey("assignments.id"))

    work_date: Mapped[date] = mapped_column(Date, index=True)
    # 三个时段选择
    has_morning: Mapped[bool] = mapped_column(Boolean, default=False)
    has_afternoon: Mapped[bool] = mapped_column(Boolean, default=False)
    has_evening: Mapped[bool] = mapped_column(Boolean, default=False)
    # 是否工作日（默认按 weekday 自动算，admin 可手动覆盖标记假日）
    is_workday: Mapped[bool] = mapped_column(Boolean, default=True)
    # 自动算出的人天值（自然 + 加权）— 持久化便于查询/聚合
    natural_days: Mapped[float] = mapped_column(Numeric(4, 2), default=0)
    weighted_days: Mapped[float] = mapped_column(Numeric(4, 2), default=0)
    description: Mapped[str | None] = mapped_column(Text)

    # 审批流：pending = 待审，approved = 已审，rejected = 已拒（有理由）
    approval_status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    reject_reason: Mapped[str | None] = mapped_column(Text)
    submitted_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # 兼容旧字段（is_approved = approval_status == 'approved'）
    is_approved: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    engineer: Mapped["Engineer"] = relationship(lazy="selectin")  # noqa: F821
    project: Mapped["Project"] = relationship(lazy="selectin")  # noqa: F821

    def recompute(self) -> None:
        """根据当前 has_* + work_date/is_workday 重算 natural_days + weighted_days。"""
        natural, weighted = compute_weighted_days(
            self.work_date, self.has_morning, self.has_afternoon, self.has_evening,
            is_workday=self.is_workday,
        )
        self.natural_days = natural
        self.weighted_days = weighted
