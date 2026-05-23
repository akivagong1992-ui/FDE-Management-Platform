"""need_party: show_in_cockpit + logo_path

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-24 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("need_parties") as batch:
        batch.add_column(sa.Column("show_in_cockpit", sa.Boolean(), nullable=False, server_default=sa.text("0")))
        batch.add_column(sa.Column("logo_path", sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("need_parties") as batch:
        batch.drop_column("logo_path")
        batch.drop_column("show_in_cockpit")
