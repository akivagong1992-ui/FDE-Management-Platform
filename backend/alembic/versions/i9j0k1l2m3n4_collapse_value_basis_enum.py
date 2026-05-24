"""value_created_basis 收成 outsource_equiv / other 两个

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-05-24 23:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'i9j0k1l2m3n4'
down_revision: Union[str, None] = 'h8i9j0k1l2m3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 4 个旧 basis 值并入 outsource_equiv（业务上都是「相当于外包成本」的变体）
    op.execute(
        """
        UPDATE projects
        SET value_created_basis = 'outsource_equiv'
        WHERE value_created_basis IN
              ('replace_audit_fee', 'avoid_penalty', 'save_hours', 'strategic_reserve')
        """
    )


def downgrade() -> None:
    # 不可逆：旧细分类型信息已合并丢失
    pass
