from pydantic import BaseModel, ConfigDict, Field


LEVEL_PATTERN = "^(L1|L2|L3)?$"


class SkillBase(BaseModel):
    name: str            # 认证名称，e.g. CCIE 路由交换
    category: str        # 网络能力 / 安全能力 / ...
    issuer: str | None = None    # 厂商，e.g. Cisco / 华为
    level: str | None = Field(default=None, pattern=LEVEL_PATTERN)  # L1-L3
    is_active: bool = True


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    issuer: str | None = None
    level: str | None = Field(default=None, pattern=LEVEL_PATTERN)
    is_active: bool | None = None


class SkillOut(SkillBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class SkillBulkItem(BaseModel):
    """批量导入一行：厂商 + 认证名称 + 等级；category 来自外层 payload"""
    issuer: str
    name: str
    level: str = Field(pattern="^(L1|L2|L3)$")


class SkillBulkImport(BaseModel):
    category: str       # 整批共用的分类
    items: list[SkillBulkItem]


class SkillBulkResult(BaseModel):
    created: int
    skipped: int        # 重名跳过
    skipped_names: list[str] = []


class EngineerSkillItem(BaseModel):
    """挂载工程师 × 认证：只需 skill_id 引用字典（等级由 Skill.level 决定）。"""

    skill_id: int
    notes: str | None = None


class EngineerSkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    skill_id: int
    skill_name: str
    skill_category: str
    skill_issuer: str | None = None
    skill_level: str | None = None  # L1-L3 from the catalog
    notes: str | None = None
