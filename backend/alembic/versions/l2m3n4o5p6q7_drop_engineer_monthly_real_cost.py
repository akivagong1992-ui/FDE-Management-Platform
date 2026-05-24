"""engineer 删除 monthly_real_cost 字段

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-05-25 09:00:00.000000

业务背景：monthly_real_cost (Vendor 真实人工成本) 字段无任何聚合计算使用 — 仅在
UI 上展示，不参与任何利润 / 成本 / 派单计算。用户决定砍掉简化模型。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'l2m3n4o5p6q7'
down_revision: Union[str, None] = 'k1l2m3n4o5p6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("engineers") as batch:
        batch.drop_column("monthly_real_cost")


def downgrade() -> None:
    with op.batch_alter_table("engineers") as batch:
        batch.add_column(sa.Column("monthly_real_cost", sa.Numeric(12, 2), nullable=True))
