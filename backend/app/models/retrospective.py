from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProjectRetrospective(Base):
    """项目复盘（README §3 维度 8）— 验收后填的满意度 + 行动项闭环。

    Phase 3-bulk 简化版：一项目可有多条复盘记录（不同时间点），最新条记入驾驶舱聚合。
    续单跟踪暂用 NeedParty 下属项目数倒推（Phase 3+ 可建独立 RenewalTracking）。
    """

    __tablename__ = "project_retrospectives"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)

    satisfaction_score: Mapped[int] = mapped_column(Integer)  # 1-5
    what_went_well: Mapped[str | None] = mapped_column(Text)
    what_to_improve: Mapped[str | None] = mapped_column(Text)
    action_items: Mapped[str | None] = mapped_column(Text)  # one per line
    next_review_date: Mapped[date | None] = mapped_column(Date)
    is_closed: Mapped[bool] = mapped_column(default=False)  # 行动项闭环

    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped["Project"] = relationship(lazy="selectin")  # noqa: F821
