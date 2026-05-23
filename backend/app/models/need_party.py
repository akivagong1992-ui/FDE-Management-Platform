from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# Enum-like
NP_TYPE_INTERNAL = "internal_dept"        # 电信集团内部部门
NP_TYPE_EXTERNAL = "external_company"     # 外部合同方


class NeedParty(Base):
    """需求方 / 客户档案 — 项目的"甲方接收人"。可以是电信内部部门或外部合同方。"""

    __tablename__ = "need_parties"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    party_type: Mapped[str] = mapped_column(String(32), default=NP_TYPE_INTERNAL)
    contact_person: Mapped[str | None] = mapped_column(String(64))
    contact_phone: Mapped[str | None] = mapped_column(String(32))
    contact_email: Mapped[str | None] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
