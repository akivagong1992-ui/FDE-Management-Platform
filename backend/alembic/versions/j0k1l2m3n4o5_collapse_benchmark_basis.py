"""benchmark_basis 收成 vendor_quote / historical_avg 两个

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-05-24 23:30:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'j0k1l2m3n4o5'
down_revision: Union[str, None] = 'i9j0k1l2m3n4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 2 个旧 basis 值并入 historical_avg（更稳妥：不假装是 vendor_quote 真实询价）
    op.execute(
        """
        UPDATE projects
        SET benchmark_basis = 'historical_avg'
        WHERE benchmark_basis IN ('industry_benchmark', 'manual_estimate')
        """
    )


def downgrade() -> None:
    # 不可逆：旧细分类型信息已合并丢失
    pass
