"""project 加 bid_outcome（投标结果）

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-05-24 22:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'h8i9j0k1l2m3'
down_revision: Union[str, None] = 'g7h8i9j0k1l2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("projects") as batch:
        batch.add_column(
            sa.Column(
                "bid_outcome",
                sa.String(16),
                nullable=False,
                server_default="pending",
            )
        )
        batch.create_index("ix_projects_bid_outcome", ["bid_outcome"], unique=False)

    # 历史数据回填：
    #  - cancelled 项目 → escaped（之前已经在 status 里表示跑单）
    #  - 有至少 1 笔 status=received 的收入项目 → won（既往逻辑里这种就是已计入 savings 的）
    #  - 其他 → pending（默认）
    op.execute("UPDATE projects SET bid_outcome = 'escaped' WHERE status = 'cancelled'")
    op.execute(
        """
        UPDATE projects
        SET bid_outcome = 'won'
        WHERE bid_outcome = 'pending'
          AND id IN (
            SELECT DISTINCT project_id FROM project_revenues
            WHERE status = 'received'
          )
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("projects") as batch:
        batch.drop_index("ix_projects_bid_outcome")
        batch.drop_column("bid_outcome")
