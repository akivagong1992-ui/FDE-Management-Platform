from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(128))
    email: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="admin")  # admin/pm/finance/engineer/lead/vendor
    # role=engineer 的用户挂到一条 Engineer 记录，决定他能看哪些派单
    engineer_id: Mapped[int | None] = mapped_column(ForeignKey("engineers.id"), index=True)
    # role=vendor 的用户挂到一个 Vendor 公司，仅能看/提交该 vendor 名下的 ExpenseRequest
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"), index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    # Feishu (Lark) integration — empty until Phase 4 actually wires SSO
    feishu_open_id: Mapped[str | None] = mapped_column(String(64), index=True)
    feishu_union_id: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
