"""project 加 summary + contact_engineer_id；新建 project_comments 表

Revision ID: o5p6q7r8s9t0
Revises: n4o5p6q7r8s9
Create Date: 2026-05-25 14:00:00.000000

业务背景：用户 2026-05-25 把 /efficiency 页（项目效率管理）升级：
- 删 时间进度 柱形图（占空间）
- 加 对接工程师（指向 engineers 表的派工人员）
- 加 项目摘要（一句话自由录入）
- 加 管理员↔工程师 评论流（互动动作）
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'o5p6q7r8s9t0'
down_revision: Union[str, None] = 'n4o5p6q7r8s9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("projects") as batch:
        batch.add_column(sa.Column("summary", sa.Text(), nullable=True))
        batch.add_column(sa.Column("contact_engineer_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_projects_contact_engineer",
            "engineers", ["contact_engineer_id"], ["id"],
        )

    op.create_table(
        "project_comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("author_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("author_role", sa.String(16), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("project_comments")
    with op.batch_alter_table("projects") as batch:
        batch.drop_constraint("fk_projects_contact_engineer", type_="foreignkey")
        batch.drop_column("contact_engineer_id")
        batch.drop_column("summary")
