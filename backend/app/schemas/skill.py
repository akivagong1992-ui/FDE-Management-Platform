from pydantic import BaseModel, ConfigDict, Field


class SkillBase(BaseModel):
    name: str
    category: str
    description: str | None = None
    is_active: bool = True


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    is_active: bool | None = None


class SkillOut(SkillBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class EngineerSkillItem(BaseModel):
    """Used to attach a skill to an engineer（level 字段已停用，仅为兼容老前端）。"""

    skill_id: int
    level: int = Field(default=0, ge=0, le=5)
    notes: str | None = None


class EngineerSkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    skill_id: int
    skill_name: str
    skill_category: str
    level: int  # 始终返回 0，前端不展示
    notes: str | None = None
