from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Skill(Base):
    """技能字典项 — e.g. Python / Java / 网络 / 通信 / 安全 / Kubernetes."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(32))  # 编程语言/网络/通信/安全/云/数据/其他
    description: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EngineerSkill(Base):
    """工程师 × 技能 多对多，含等级（L1-L5）。"""

    __tablename__ = "engineer_skills"
    __table_args__ = (UniqueConstraint("engineer_id", "skill_id", name="uq_engineer_skill"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineers.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    level: Mapped[int] = mapped_column(Integer, default=1)  # 1~5
    notes: Mapped[str | None] = mapped_column(String(255))

    skill: Mapped["Skill"] = relationship(lazy="selectin")
