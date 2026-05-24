from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Skill(Base):
    """技能 / 认证字典项 — 用户 2026-05-25 重构：
    每条记录是一个「认证 + 等级」组合，e.g. (CCIE 路由交换, Cisco, 网络能力, L3)。
    工程师挂技能 = 引用这里某一条 → 自动带出 厂商 + 等级。
    """

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # 认证名称 e.g. CCIE 路由交换
    category: Mapped[str] = mapped_column(String(32))  # 网络能力/安全能力/弱电能力/云能力/数据能力/AI 能力
    issuer: Mapped[str | None] = mapped_column(String(64))  # 厂商 e.g. Cisco / 华为 / CNCF
    level: Mapped[str | None] = mapped_column(String(4))    # L1 / L2 / L3
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EngineerSkill(Base):
    """工程师 × 技能 多对多，含等级（已停用 — 只保留会/不会标记，由 cert_level 替代）。"""

    __tablename__ = "engineer_skills"
    __table_args__ = (UniqueConstraint("engineer_id", "skill_id", name="uq_engineer_skill"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineers.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    level: Mapped[int] = mapped_column(Integer, default=1)  # 1~5
    notes: Mapped[str | None] = mapped_column(String(255))

    skill: Mapped["Skill"] = relationship(lazy="selectin")
