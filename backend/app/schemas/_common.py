"""共享 schema 类型与 validator。"""
from typing import Annotated, Any

from pydantic import BeforeValidator, EmailStr


def _empty_str_to_none(v: Any) -> Any:
    """把空字符串 / 纯空白字符串转成 None。前端表单留空时通常发 ""，pydantic 严格类型
    （EmailStr 等）会拒收，转成 None 让 Optional 字段正常落库。
    """
    if isinstance(v, str) and v.strip() == "":
        return None
    return v


# 用法：email: OptionalEmail = None
OptionalEmail = Annotated[EmailStr | None, BeforeValidator(_empty_str_to_none)]

# 用法：code: OptionalStr = None  —— 留空时 None 入库，避免空串撞 UNIQUE 索引
OptionalStr = Annotated[str | None, BeforeValidator(_empty_str_to_none)]
