from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class NeedPartyBase(BaseModel):
    name: str
    party_type: str = Field(default="internal_dept", pattern="^(internal_dept|external_company)$")
    contact_person: str | None = None
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    notes: str | None = None


class NeedPartyCreate(NeedPartyBase):
    pass


class NeedPartyUpdate(BaseModel):
    name: str | None = None
    party_type: str | None = Field(default=None, pattern="^(internal_dept|external_company)$")
    contact_person: str | None = None
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    notes: str | None = None


class NeedPartyOut(NeedPartyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
