"""expense_requests 加两段式审批字段：vendor 阶段 + lead 阶段

Revision ID: r8s9t0u1v2w3
Revises: q7r8s9t0u1v2
Create Date: 2026-05-28 12:00:00.000000

业务背景：engineer 自己提交的报销，先由所选 vendor 审批，再由 lead 审批；
vendor 自己提交的（替工程师录入）跳过 vendor 阶段，直接 lead 审批。

新增字段：
- approval_stage: 'vendor' 或 'lead'，当前审批阶段或终态时停留的阶段
- vendor_approved_at / vendor_approved_by_user_id / vendor_approval_note: vendor 阶段批准时记录

存量数据回填：
- 之前所有 expense 都是 vendor 提交的（engineer 提交是本次新增能力），
  pending 的全部置 stage='lead'；non-pending 同样置 'lead'（不影响终态）
- 极少数测试期 e1/e2 提交的 pending 单也归 'lead' —— 简化迁移，不需要 join users
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'r8s9t0u1v2w3'
down_revision: Union[str, None] = 'q7r8s9t0u1v2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "expense_requests",
        sa.Column("approval_stage", sa.String(16), nullable=True),
    )
    op.add_column(
        "expense_requests",
        sa.Column("vendor_approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "expense_requests",
        sa.Column("vendor_approved_by_user_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "expense_requests",
        sa.Column("vendor_approval_note", sa.Text(), nullable=True),
    )
    op.create_foreign_key(
        "fk_expense_requests_vendor_approved_by_user_id",
        "expense_requests",
        "users",
        ["vendor_approved_by_user_id"],
        ["id"],
    )

    # 存量回填：engineer 提交且仍 pending 的归 vendor 阶段；其余一律 lead 阶段
    op.execute("""
        UPDATE expense_requests AS er
        SET approval_stage = 'vendor'
        FROM users AS u
        WHERE er.requested_by_user_id = u.id
          AND u.role = 'engineer'
          AND er.status = 'pending'
    """)
    op.execute(
        "UPDATE expense_requests SET approval_stage = 'lead' WHERE approval_stage IS NULL"
    )
    op.alter_column("expense_requests", "approval_stage", nullable=False)


def downgrade() -> None:
    op.drop_constraint(
        "fk_expense_requests_vendor_approved_by_user_id",
        "expense_requests",
        type_="foreignkey",
    )
    op.drop_column("expense_requests", "vendor_approval_note")
    op.drop_column("expense_requests", "vendor_approved_by_user_id")
    op.drop_column("expense_requests", "vendor_approved_at")
    op.drop_column("expense_requests", "approval_stage")
