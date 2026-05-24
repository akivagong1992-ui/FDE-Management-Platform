"""project_revenue 加 non_service_expense（非服务开销）

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-05-24 23:50:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'k1l2m3n4o5p6'
down_revision: Union[str, None] = 'j0k1l2m3n4o5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("project_revenues") as batch:
        batch.add_column(sa.Column("non_service_expense", sa.Numeric(14, 2), nullable=True))

    # 历史数据回填：典型业务里非服务开销约占客户付款 70%
    # 用 gross_amount × 0.70 估算，缺 gross 的设 NULL
    op.execute(
        """
        UPDATE project_revenues
        SET non_service_expense = ROUND(gross_amount * 0.70, 2)
        WHERE gross_amount IS NOT NULL AND non_service_expense IS NULL
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("project_revenues") as batch:
        batch.drop_column("non_service_expense")
