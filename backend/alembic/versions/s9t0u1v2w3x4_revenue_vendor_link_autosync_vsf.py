"""ProjectRevenue 加 vendor_id（必填）；存量数据回填到唯一 vendor；清理孤儿 VSF，
按 ProjectRevenue 重建镜像 VSF。

Revision ID: s9t0u1v2w3x4
Revises: r8s9t0u1v2w3
Create Date: 2026-05-28 12:00:00.000000

业务背景（Akiva 2026-05-28 确认）：
- pass-through 100%：每笔 ProjectRevenue 都强制选择"经办 Vendor"
- VSF 不再独立录入，而是由 ProjectRevenue 自动镜像（同 project + 同 vendor + 同 amount）
- 多 vendor 项目通过录多条 ProjectRevenue 实现，每条挂自己的 vendor
- 利润公式不变：team_margin = Σ VSF − Σ 全部支出（仍然成立，因为 VSF = Σ revenue）

迁移行为：
1. 加 vendor_id 列（先 nullable 以便回填）
2. 把所有现有 ProjectRevenue 的 vendor_id 设为系统里第一个 vendor 的 id
3. 加 NOT NULL 约束
4. 清空 vendor_service_fees 表（之前可能有手动录入的孤儿/重复数据）
5. 按 ProjectRevenue 自动批量插入对应的 VSF 镜像
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 's9t0u1v2w3x4'
down_revision: Union[str, None] = 'r8s9t0u1v2w3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) 加 vendor_id 列
    op.add_column(
        "project_revenues",
        sa.Column("vendor_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_project_revenues_vendor_id",
        "project_revenues", "vendors",
        ["vendor_id"], ["id"],
    )
    op.create_index(
        "ix_project_revenues_vendor_id",
        "project_revenues", ["vendor_id"],
    )

    # 2) 回填：所有现有 ProjectRevenue 的 vendor_id 设为系统里第一个 vendor
    #    （如果系统没 vendor 则跳过，alter NOT NULL 会失败，提示先建 vendor）
    op.execute("""
        UPDATE project_revenues
        SET vendor_id = (SELECT id FROM vendors ORDER BY id LIMIT 1)
        WHERE vendor_id IS NULL
    """)

    # 3) NOT NULL 约束
    op.alter_column("project_revenues", "vendor_id", nullable=False)

    # 4) 清空 vendor_service_fees（之前可能的手动录入数据）
    op.execute("TRUNCATE TABLE vendor_service_fees RESTART IDENTITY CASCADE")

    # 5) 按 ProjectRevenue 自动重建 VSF 镜像
    op.execute("""
        INSERT INTO vendor_service_fees (
            project_id, vendor_id, amount, currency,
            fee_type, period_start, period_end,
            paid_at, status, description, created_at, updated_at
        )
        SELECT
            pr.project_id, pr.vendor_id, pr.amount, pr.currency,
            'project_milestone', pr.recognized_date, pr.recognized_date,
            NULL, 'draft', '自动镜像自 ProjectRevenue (pass-through)',
            NOW(), NOW()
        FROM project_revenues pr
    """)


def downgrade() -> None:
    op.execute("DELETE FROM vendor_service_fees WHERE description = '自动镜像自 ProjectRevenue (pass-through)'")
    op.drop_index("ix_project_revenues_vendor_id", table_name="project_revenues")
    op.drop_constraint("fk_project_revenues_vendor_id", "project_revenues", type_="foreignkey")
    op.drop_column("project_revenues", "vendor_id")
