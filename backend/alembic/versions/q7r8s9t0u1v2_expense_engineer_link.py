"""expense_requests 加 engineer_id：vendor 提交时可选择受益工程师

Revision ID: q7r8s9t0u1v2
Revises: p6q7r8s9t0u1
Create Date: 2026-05-28 10:00:00.000000

业务背景：vendor 替工程师录入差旅/培训/耗材等垫付报销时，需要标明这笔钱是哪个
工程师产生的；lead 审批时也要看得见受益人。字段 nullable —— 项目层级支出
（材料/许可证/分包等）不一定关联到具体工程师。
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'q7r8s9t0u1v2'
down_revision: Union[str, None] = 'p6q7r8s9t0u1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "expense_requests",
        sa.Column("engineer_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_expense_requests_engineer_id",
        "expense_requests",
        "engineers",
        ["engineer_id"],
        ["id"],
    )
    op.create_index(
        "ix_expense_requests_engineer_id",
        "expense_requests",
        ["engineer_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_expense_requests_engineer_id", table_name="expense_requests")
    op.drop_constraint("fk_expense_requests_engineer_id", "expense_requests", type_="foreignkey")
    op.drop_column("expense_requests", "engineer_id")
