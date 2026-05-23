from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# 派单生命周期状态（PM 视角的派单阶段）
ASSIGNMENT_STATUS_PLANNED = "planned"
ASSIGNMENT_STATUS_IN_PROGRESS = "in_progress"
ASSIGNMENT_STATUS_ENDED = "ended"
ASSIGNMENT_STATUS_CANCELLED = "cancelled"

# 工程师确认状态（双向流转）
APPROVAL_PENDING = "pending"      # 已派，待工程师接受/拒绝
APPROVAL_ACCEPTED = "accepted"    # 工程师已接单
APPROVAL_REJECTED = "rejected"    # 工程师已拒单（PM 需重派新单给别人）
APPROVAL_STATUSES = (APPROVAL_PENDING, APPROVAL_ACCEPTED, APPROVAL_REJECTED)


class Assignment(Base):
    """派单 — 工程师 × 项目 × 时段 × 角色。

    取消 allocation_ratio（工时占比无客观定义），改用接 / 拒 / 留言三方双向流转。
    """

    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    engineer_id: Mapped[int] = mapped_column(ForeignKey("engineers.id"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)

    role: Mapped[str | None] = mapped_column(String(64))  # e.g. 开发/测试/PM/架构师
    planned_start_date: Mapped[date | None] = mapped_column(Date)
    planned_end_date: Mapped[date | None] = mapped_column(Date)
    actual_start_date: Mapped[date | None] = mapped_column(Date)
    actual_end_date: Mapped[date | None] = mapped_column(Date)

    status: Mapped[str] = mapped_column(String(16), default=ASSIGNMENT_STATUS_PLANNED, index=True)
    approval_status: Mapped[str] = mapped_column(String(16), default=APPROVAL_PENDING, index=True)
    notes: Mapped[str | None] = mapped_column(Text)

    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    engineer_responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    engineer: Mapped["Engineer"] = relationship(lazy="selectin")  # noqa: F821
    project: Mapped["Project"] = relationship(lazy="selectin")  # noqa: F821
    messages: Mapped[list["AssignmentMessage"]] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="AssignmentMessage.created_at",
    )


# AssignmentMessage 发送方分类
MSG_FROM_SYSTEM = "system"   # 派单创建 / 状态变更等自动消息
MSG_FROM_PM = "pm"           # 管理者方（lead / admin / pm）
MSG_FROM_ENGINEER = "engineer"


class AssignmentMessage(Base):
    """派单对话留痕 — PM 与工程师双向沟通。"""

    __tablename__ = "assignment_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    sender_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    sender_kind: Mapped[str] = mapped_column(String(16))  # system / pm / engineer
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
