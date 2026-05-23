from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# Channels (matches NotificationService.CHANNELS)
CHANNEL_LOG = "log"
CHANNEL_FEISHU = "feishu"
CHANNEL_EMAIL = "email"  # 预留

# Status
DELIVERY_OK = "ok"
DELIVERY_NOT_IMPLEMENTED = "not_implemented"
DELIVERY_ERROR = "error"


class NotificationLog(Base):
    """每次发出的通知留痕——用于审计 + 后续接入真飞书时的回放素材。"""

    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)  # expense.submitted / retro.created / ...
    channel: Mapped[str] = mapped_column(String(16), index=True)     # log / feishu / email
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(String(512))

    target_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    target_role: Mapped[str | None] = mapped_column(String(32))      # role-based broadcast
    triggered_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    status: Mapped[str] = mapped_column(String(16), default=DELIVERY_OK)
    error_detail: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
