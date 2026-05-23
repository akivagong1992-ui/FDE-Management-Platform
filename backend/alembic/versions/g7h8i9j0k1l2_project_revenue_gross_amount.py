"""project_revenue 加 gross_amount（客户付款总额）

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9dabc
Create Date: 2026-05-24 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, None] = 'f6a7b8c9dabc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("project_revenues") as batch:
        batch.add_column(sa.Column("gross_amount", sa.Numeric(14, 2), nullable=True))

    # 历史数据：缺省假设客户付款总额 = 团队入账（即不存在销售切除）
    # 用户后续可手动回填真实 gross_amount
    op.execute("UPDATE project_revenues SET gross_amount = amount WHERE gross_amount IS NULL")


def downgrade() -> None:
    with op.batch_alter_table("project_revenues") as batch:
        batch.drop_column("gross_amount")
