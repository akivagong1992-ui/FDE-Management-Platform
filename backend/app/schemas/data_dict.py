from pydantic import BaseModel, ConfigDict


class DataDictBase(BaseModel):
    category: str
    code: str
    label: str
    sort_order: int = 0
    is_active: bool = True


class DataDictCreate(DataDictBase):
    pass


class DataDictUpdate(BaseModel):
    label: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class DataDictOut(DataDictBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
