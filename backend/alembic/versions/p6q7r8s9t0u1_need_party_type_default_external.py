"""need_party.party_type 默认值改外部客户类型 + 转换存量 internal_dept/external_company 数据

Revision ID: p6q7r8s9t0u1
Revises: o5p6q7r8s9t0
Create Date: 2026-05-26 10:00:00.000000

业务背景：PLAN §0 A3 校准——电信HK 项目全部对外（外资企业 / 港企 / 跨国公司 / 政府机构 / 银行 / ...），
不含集团内部门。前端 CLIENT_TYPES 早已倒向外部分类，schema 默认 "外资企业"，
但 model 默认仍是旧 internal_dept；本 migration 把存量数据和 server default 同步过来。

转换规则：
- internal_dept → 外资企业（保守默认；admin 可手动改正）
- external_company → 外资企业（同上）
- 其他保持不变（已经是 CLIENT_TYPES 字符串）
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'p6q7r8s9t0u1'
down_revision: Union[str, None] = 'o5p6q7r8s9t0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE need_parties SET party_type = '外资企业' "
        "WHERE party_type IN ('internal_dept', 'external_company')"
    )


def downgrade() -> None:
    # 无法精确还原（信息已丢失）；不动数据，仅留 noop
    pass
