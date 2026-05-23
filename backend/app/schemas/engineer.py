from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.skill import EngineerSkillOut


class CertificateIn(BaseModel):
    name: str
    issuer: str | None = None
    cert_number: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    file_path: str | None = None
    cert_level: str | None = Field(default=None, pattern="^(L1|L2|L3)?$")
    cert_category: str | None = None


class CertificateOut(CertificateIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class EngineerBase(BaseModel):
    vendor_id: int
    employment_form: str = Field(pattern="^(vendor_direct|vendor_via_labor)$")
    labor_company: str | None = None

    full_name: str
    english_name: str | None = None
    gender: str | None = None
    birth_date: date | None = None
    mobile: str | None = None
    email: EmailStr | None = None

    id_doc_type: str | None = Field(default=None, pattern="^(HKID|passport|mainland_id)?$")
    status: str = "reserved"
    entry_date: date | None = None
    exit_date: date | None = None
    notes: str | None = None


class EngineerCreate(EngineerBase):
    id_doc_number: str | None = None  # plaintext input; service layer encrypts
    monthly_cost_to_telecom: Decimal | None = None
    monthly_real_cost: Decimal | None = None  # ignored if caller is not lead/finance


class EngineerUpdate(BaseModel):
    vendor_id: int | None = None
    employment_form: str | None = Field(default=None, pattern="^(vendor_direct|vendor_via_labor)$")
    labor_company: str | None = None
    full_name: str | None = None
    english_name: str | None = None
    gender: str | None = None
    birth_date: date | None = None
    mobile: str | None = None
    email: EmailStr | None = None
    id_doc_type: str | None = None
    id_doc_number: str | None = None
    status: str | None = None
    entry_date: date | None = None
    exit_date: date | None = None
    notes: str | None = None
    monthly_cost_to_telecom: Decimal | None = None
    monthly_real_cost: Decimal | None = None


class EngineerOut(EngineerBase):
    """List/detail view. ID number is always masked here; cost fields are nullable."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    vendor_name: str | None = None
    id_doc_number_masked: str = ""

    # Cost fields — for privileged roles only; otherwise None
    monthly_cost_to_telecom: Decimal | None = None
    monthly_real_cost: Decimal | None = None

    skills: list[EngineerSkillOut] = []
    certificates: list[CertificateOut] = []

    created_at: datetime


class EngineerSensitiveOut(BaseModel):
    """Reveal endpoint — returns decrypted ID number. Only lead/admin allowed."""

    id: int
    id_doc_type: str | None = None
    id_doc_number: str | None = None
