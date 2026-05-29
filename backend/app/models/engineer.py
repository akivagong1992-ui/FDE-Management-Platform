from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# Enum-like string columns (kept as strings for SQLite/Postgres portability)
EMPLOYMENT_FORM_VENDOR_DIRECT = "vendor_direct"          # Vendor 直签
EMPLOYMENT_FORM_VENDOR_VIA_LABOR = "vendor_via_labor"    # Vendor 通过劳务公司签

ID_DOC_HKID = "HKID"
ID_DOC_PASSPORT = "passport"
ID_DOC_MAINLAND = "mainland_id"

# 工程师在职状态：2 态简化（reserved / pending 已废除，迁移合并到 active）
STATUS_ACTIVE = "active"      # 在职
STATUS_DEPARTED = "departed"  # 已离职
ENGINEER_STATUSES = (STATUS_ACTIVE, STATUS_DEPARTED)


class Engineer(Base):
    """外包工程师档案。归属 Vendor。"""

    __tablename__ = "engineers"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 归属
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    employment_form: Mapped[str] = mapped_column(String(32))  # vendor_direct / vendor_via_labor
    labor_company: Mapped[str | None] = mapped_column(String(128))  # 仅 vendor_via_labor 时填写

    # 基本信息
    full_name: Mapped[str] = mapped_column(String(64), index=True)
    english_name: Mapped[str | None] = mapped_column(String(64))
    gender: Mapped[str | None] = mapped_column(String(8))  # M/F/Other
    birth_date: Mapped[date | None] = mapped_column(Date)
    mobile: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(128))

    # 证件（敏感字段：DB 内 AES-GCM 加密；非负责人/管理员看不到原文）
    id_doc_type: Mapped[str | None] = mapped_column(String(16))  # HKID/passport/mainland_id
    id_doc_number_enc: Mapped[str | None] = mapped_column(Text)  # ciphertext (base64)

    # 级别 / 状态
    level: Mapped[int | None] = mapped_column(default=2)  # L1-L3（已停用，cert_level 取代）
    status: Mapped[str] = mapped_column(String(16), default=STATUS_ACTIVE)
    entry_date: Mapped[date | None] = mapped_column(Date)
    exit_date: Mapped[date | None] = mapped_column(Date)

    # 成本（仅财务/负责人可见 — API 层按角色过滤）
    monthly_cost_to_telecom: Mapped[float | None] = mapped_column(Numeric(12, 2))  # 电信付给 Vendor 的月服务费

    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vendor: Mapped["Vendor"] = relationship(lazy="selectin")  # noqa: F821
    skills: Mapped[list["EngineerSkill"]] = relationship(  # noqa: F821
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
