from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas._common import OptionalEmail


class VendorBase(BaseModel):
    name: str
    short_name: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    contact_email: OptionalEmail = None
    payment_terms: str | None = None
    cooperation_status: str = "active"
    notes: str | None = None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: str | None = None
    short_name: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    contact_email: OptionalEmail = None
    payment_terms: str | None = None
    cooperation_status: str | None = None
    notes: str | None = None


class VendorOut(VendorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
