from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas._common import OptionalEmail


# 角色清单（保持与代码 require_role / _can_view_cost 一致）
ROLE_PATTERN = "^(admin|lead|pm|finance|engineer|vendor)$"


class UserBase(BaseModel):
    username: str
    full_name: str | None = None
    email: OptionalEmail = None
    role: str = Field(default="admin", pattern=ROLE_PATTERN)
    is_active: bool = True
    engineer_id: int | None = None  # role=engineer 用
    vendor_id: int | None = None    # role=vendor 用


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: OptionalEmail = None
    role: str | None = Field(default=None, pattern=ROLE_PATTERN)
    is_active: bool | None = None
    password: str | None = None
    engineer_id: int | None = None
    vendor_id: int | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
