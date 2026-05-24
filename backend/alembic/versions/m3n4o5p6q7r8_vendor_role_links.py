"""user + expense_request 加 vendor_id (vendor 角色用)

Revision ID: m3n4o5p6q7r8
Revises: l2m3n4o5p6q7
Create Date: 2026-05-25 10:00:00.000000

业务背景：新增 vendor 角色 — vendor 公司自己进系统提「我要花这笔钱」的申请，
admin 这边审批。
- users.vendor_id：标记某用户属于哪个 vendor 公司（仅 role=vendor 时设置）
- expense_requests.vendor_id：标记此 expense 由哪个 vendor 提交
  vendor 用户列表时按此过滤；admin 不过滤可见全部
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'm3n4o5p6q7r8'
down_revision: Union[str, None] = 'l2m3n4o5p6q7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("vendor_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_users_vendor", "vendors", ["vendor_id"], ["id"])
        batch.create_index("ix_users_vendor_id", ["vendor_id"], unique=False)

    with op.batch_alter_table("expense_requests") as batch:
        batch.add_column(sa.Column("vendor_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_expense_requests_vendor", "vendors", ["vendor_id"], ["id"])
        batch.create_index("ix_expense_requests_vendor_id", ["vendor_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("expense_requests") as batch:
        batch.drop_index("ix_expense_requests_vendor_id")
        batch.drop_constraint("fk_expense_requests_vendor", type_="foreignkey")
        batch.drop_column("vendor_id")
    with op.batch_alter_table("users") as batch:
        batch.drop_index("ix_users_vendor_id")
        batch.drop_constraint("fk_users_vendor", type_="foreignkey")
        batch.drop_column("vendor_id")
