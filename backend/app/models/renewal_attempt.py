from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


RENEWAL_OUTCOME_PENDING = "pending"
RENEWAL_OUTCOME_WON = "won"
RENEWAL_OUTCOME_LOST = "lost"

# Lost reason taxonomy (Phase 3-next-iii Round 2)
LOST_REASON_OUTSOURCE = "lost_to_outsource"   # 输给传统外包
LOST_REASON_PRICE = "price"                   # 价格因素
LOST_REASON_QUALITY = "quality"               # 质量 / 满意度问题
LOST_REASON_NO_BUDGET = "no_budget"           # 客户没预算
LOST_REASON_INTERNAL = "internal_hire"        # 客户自建团队
LOST_REASON_OTHER = "other"


class RenewalAttempt(Base):
    """续单尝试跟踪 — 与 Project.renewal_of_project_id 互补：
    成功的续单会同时有 RenewalAttempt(outcome=won) + 一个新 Project 标记 renewal_of_project_id；
    失败的续单只有 RenewalAttempt(outcome=lost)，没有新 Project。
    """

    __tablename__ = "renewal_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    previous_project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    attempt_date: Mapped[date] = mapped_column(Date)

    outcome: Mapped[str] = mapped_column(String(16), default=RENEWAL_OUTCOME_PENDING, index=True)
    won_project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))  # only if outcome=won
    lost_reason: Mapped[str | None] = mapped_column(String(32))                    # only if outcome=lost
    lost_reason_note: Mapped[str | None] = mapped_column(Text)

    notes: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    previous_project: Mapped["Project"] = relationship(  # noqa: F821
        foreign_keys=[previous_project_id], lazy="selectin",
    )
    won_project: Mapped["Project | None"] = relationship(  # noqa: F821
        foreign_keys=[won_project_id], lazy="selectin",
    )
