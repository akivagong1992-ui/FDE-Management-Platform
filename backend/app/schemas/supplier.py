from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class SupplierBase(BaseModel):
    name: str
    category: str | None = None  # 耗材/分包/临时人力/许可/差旅/综合
    contact_person: str | None = None
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    payment_terms: str | None = None
    is_active: bool = True
    notes: str | None = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    payment_terms: str | None = None
    is_active: bool | None = None
    notes: str | None = None


class SupplierOut(SupplierBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
