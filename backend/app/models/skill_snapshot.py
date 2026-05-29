from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EngineerSkillSnapshot(Base):
    """工程师能力快照 — 每季度（或手动触发）保存一份，绘成长曲线（PLAN §4.8）。"""

    __tablename__ = "engineer_skill_snapshots"
    __table_args__ = (
        UniqueConstraint("engineer_id", "snapshot_date", name="uq_eng_snapshot_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineers.id"), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)

    # Snapshot 数值
    skill_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_level: Mapped[float] = mapped_column(Numeric(3, 2), default=0)  # 平均认证难度（Skill.level：L1=1/L2=2/L3=3）
    level: Mapped[int | None] = mapped_column(Integer)  # 工程师当时级别 L1-L3

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    engineer: Mapped["Engineer"] = relationship(lazy="selectin")  # noqa: F821
