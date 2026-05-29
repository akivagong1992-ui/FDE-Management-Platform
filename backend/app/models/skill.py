from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Skill(Base):
    """技能 / 认证字典 — admin 在「能力矩阵管理」Tab 集中维护的全局词库。
    每条 = 一个「认证 + 难度」组合，e.g. (CCIE 路由交换, 网络能力, Cisco, L3)。
    工程师持有认证 = 引用本字典某一条；level 是认证内禀难度，不随工程师变。
    """

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # 认证名称 e.g. CCIE 路由交换
    category: Mapped[str] = mapped_column(String(32))  # 网络能力/安全能力/弱电能力/云能力/数据能力/AI 能力
    issuer: Mapped[str | None] = mapped_column(String(64))  # 厂商 e.g. Cisco / 华为 / CNCF
    level: Mapped[str | None] = mapped_column(String(4))    # L1 初级 / L2 中级 / L3 高级（认证内禀难度）
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EngineerSkill(Base):
    """工程师 × 认证 多对多挂载（"该工程师持有这条认证"）。
    等级走 Skill.level（认证内禀属性），此表不存等级；可选 notes 备注。
    """

    __tablename__ = "engineer_skills"
    __table_args__ = (UniqueConstraint("engineer_id", "skill_id", name="uq_engineer_skill"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineers.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    notes: Mapped[str | None] = mapped_column(String(255))

    skill: Mapped["Skill"] = relationship(lazy="selectin")
