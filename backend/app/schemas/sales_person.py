from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class SalesPersonBase(BaseModel):
    name: str
    employee_id: str | None = None
    department: str | None = None
    email: EmailStr | None = None
    mobile: str | None = None
    is_active: bool = True
    notes: str | None = None


class SalesPersonCreate(SalesPersonBase):
    pass


class SalesPersonUpdate(BaseModel):
    name: str | None = None
    employee_id: str | None = None
    department: str | None = None
    email: EmailStr | None = None
    mobile: str | None = None
    is_active: bool | None = None
    notes: str | None = None


class SalesPersonOut(SalesPersonBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
