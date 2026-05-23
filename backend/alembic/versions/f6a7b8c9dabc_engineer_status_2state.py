"""engineer.status: 4 态简化为 2 态 (active / departed)

Revision ID: f6a7b8c9dabc
Revises: e5f6a7b8c9da
Create Date: 2026-05-24 15:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'f6a7b8c9dabc'
down_revision: Union[str, None] = 'e5f6a7b8c9da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # reserved / pending → active；departed 保持不变
    op.execute("""
        UPDATE engineers
        SET status = 'active'
        WHERE status IN ('reserved', 'pending')
    """)


def downgrade() -> None:
    # 不可逆 — reserved / pending 区分信息已丢失
    pass
