"""assignment 双向确认流转 + 对话留痕 + User.engineer_id

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-24 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) assignments: drop allocation_ratio + add approval_status + add audit cols
    with op.batch_alter_table("assignments") as batch:
        batch.drop_column("allocation_ratio")
        batch.add_column(sa.Column("approval_status", sa.String(length=16),
                                   nullable=False, server_default="accepted"))
        # 现有历史派单视为「已接受」，避免一上线全部变 pending 误导
        batch.add_column(sa.Column("created_by_user_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("engineer_responded_at",
                                   sa.DateTime(timezone=True), nullable=True))
        batch.create_index("ix_assignments_approval_status", ["approval_status"])
        batch.create_foreign_key("fk_assignments_created_by_user",
                                 "users", ["created_by_user_id"], ["id"])

    # 2) users: 加 engineer_id FK（engineer 角色用户绑定到一条 Engineer 记录）
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("engineer_id", sa.Integer(), nullable=True))
        batch.create_index("ix_users_engineer_id", ["engineer_id"])
        batch.create_foreign_key("fk_users_engineer", "engineers",
                                 ["engineer_id"], ["id"])

    # 3) assignment_messages 新表
    op.create_table(
        "assignment_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("sender_user_id", sa.Integer(), nullable=True),
        sa.Column("sender_kind", sa.String(length=16), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"],
                                ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_user_id"], ["users.id"]),
    )
    op.create_index("ix_assignment_messages_assignment_id",
                    "assignment_messages", ["assignment_id"])


def downgrade() -> None:
    op.drop_index("ix_assignment_messages_assignment_id",
                  table_name="assignment_messages")
    op.drop_table("assignment_messages")
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("fk_users_engineer", type_="foreignkey")
        batch.drop_index("ix_users_engineer_id")
        batch.drop_column("engineer_id")
    with op.batch_alter_table("assignments") as batch:
        batch.drop_constraint("fk_assignments_created_by_user",
                              type_="foreignkey")
        batch.drop_index("ix_assignments_approval_status")
        batch.drop_column("engineer_responded_at")
        batch.drop_column("created_by_user_id")
        batch.drop_column("approval_status")
        batch.add_column(sa.Column("allocation_ratio", sa.Integer(),
                                   nullable=False, server_default="100"))
