"""cert levels (L1/L2/L3 + category) + clear personal-rating fields

Revision ID: a1b2c3d4e5f6
Revises: f8540d2f6dcd
Create Date: 2026-05-23 23:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f8540d2f6dcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Add vendor-cert level + category columns on certificates
    with op.batch_alter_table("certificates") as batch:
        batch.add_column(sa.Column("cert_level", sa.String(length=4), nullable=True))
        batch.add_column(sa.Column("cert_category", sa.String(length=16), nullable=True))

    # 2) Zero out per-person ratings (user decision: 评级太主观，清空)
    op.execute("UPDATE engineers SET level = NULL")
    op.execute("UPDATE engineer_skills SET level = 0")


def downgrade() -> None:
    with op.batch_alter_table("certificates") as batch:
        batch.drop_column("cert_category")
        batch.drop_column("cert_level")
    # 等级数据已抹除，无法可靠还原 — downgrade 只回滚表结构
