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
    """Used to attach a skill+level to an engineer."""

    skill_id: int
    level: int = Field(ge=1, le=5)
    notes: str | None = None


class EngineerSkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    skill_id: int
    skill_name: str
    skill_category: str
    level: int
    notes: str | None = None
