"""timesheet: approval_status + reject_reason + submitted_by

Revision ID: e5f6a7b8c9da
Revises: d4e5f6a7b8c9
Create Date: 2026-05-24 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9da'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("timesheets") as batch:
        batch.add_column(sa.Column("approval_status", sa.String(length=16),
                                   nullable=False, server_default="pending"))
        batch.add_column(sa.Column("reject_reason", sa.Text(), nullable=True))
        batch.add_column(sa.Column("submitted_by_user_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_index("ix_timesheets_approval_status", ["approval_status"])
        batch.create_foreign_key("fk_timesheets_submitted_by",
                                 "users", ["submitted_by_user_id"], ["id"])
        batch.create_foreign_key("fk_timesheets_reviewed_by",
                                 "users", ["reviewed_by_user_id"], ["id"])

    # 兼容旧 is_approved：true 行迁移为 approved，否则 pending
    op.execute("""
        UPDATE timesheets
        SET approval_status = CASE WHEN is_approved = 1 THEN 'approved' ELSE 'pending' END,
            reviewed_at = approved_at
    """)


def downgrade() -> None:
    with op.batch_alter_table("timesheets") as batch:
        batch.drop_constraint("fk_timesheets_reviewed_by", type_="foreignkey")
        batch.drop_constraint("fk_timesheets_submitted_by", type_="foreignkey")
        batch.drop_index("ix_timesheets_approval_status")
        batch.drop_column("reviewed_at")
        batch.drop_column("reviewed_by_user_id")
        batch.drop_column("submitted_by_user_id")
        batch.drop_column("reject_reason")
        batch.drop_column("approval_status")
