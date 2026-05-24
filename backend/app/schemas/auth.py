from pydantic import BaseModel


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    user_id: int
    engineer_id: int | None = None  # 仅 engineer 角色用户有值
    vendor_id: int | None = None    # 仅 vendor 角色用户有值
