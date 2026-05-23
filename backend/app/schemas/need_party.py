from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class NeedPartyBase(BaseModel):
    name: str
    party_type: str = Field(default="外资企业")  # 自由字符串，由前端 CLIENT_TYPES 下拉约束
    contact_person: str | None = None
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    notes: str | None = None
    show_in_cockpit: bool = False
    logo_path: str | None = None


class NeedPartyCreate(NeedPartyBase):
    pass


class NeedPartyUpdate(BaseModel):
    name: str | None = None
    party_type: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    notes: str | None = None
    show_in_cockpit: bool | None = None
    logo_path: str | None = None


class NeedPartyOut(NeedPartyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
