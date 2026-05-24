"""skill 表 重构：删 description，加 issuer + level

Revision ID: n4o5p6q7r8s9
Revises: m3n4o5p6q7r8
Create Date: 2026-05-25 11:00:00.000000

业务背景：用户 2026-05-25 把 Skill 字典升级为「认证+等级」目录。
每条记录是一个具体的认证（如 CCIE 路由交换 / 思科 / L3），工程师挂技能 = 引用这条认证。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'n4o5p6q7r8s9'
down_revision: Union[str, None] = 'm3n4o5p6q7r8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("skills") as batch:
        batch.add_column(sa.Column("issuer", sa.String(64), nullable=True))
        batch.add_column(sa.Column("level", sa.String(4), nullable=True))
        batch.drop_column("description")


def downgrade() -> None:
    with op.batch_alter_table("skills") as batch:
        batch.add_column(sa.Column("description", sa.String(255), nullable=True))
        batch.drop_column("level")
        batch.drop_column("issuer")
