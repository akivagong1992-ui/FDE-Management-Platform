from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# party_type 默认值（前端 CLIENT_TYPES 下拉约束，自由字符串）
# 电信HK 项目全部对外（PLAN §0 A3），不含集团内部门
NP_DEFAULT_TYPE = "外资企业"

# 旧常量保留仅为向后兼容老数据，禁止用于新代码
NP_TYPE_INTERNAL = "internal_dept"        # DEPRECATED
NP_TYPE_EXTERNAL = "external_company"     # DEPRECATED


class NeedParty(Base):
    """需求方 / 客户档案 — 全部为外部客户公司（外资企业 / 港企 / 跨国 / 政府机构 / 银行 等）。"""

    __tablename__ = "need_parties"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    party_type: Mapped[str] = mapped_column(String(32), default=NP_DEFAULT_TYPE)
    contact_person: Mapped[str | None] = mapped_column(String(64))
    contact_phone: Mapped[str | None] = mapped_column(String(32))
    contact_email: Mapped[str | None] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text)

    # 驾驶舱展示控制
    show_in_cockpit: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否在驾驶舱已交付客户区展示
    logo_path: Mapped[str | None] = mapped_column(String(255))  # uploads 相对路径，对应 /api/uploads/<path>

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
