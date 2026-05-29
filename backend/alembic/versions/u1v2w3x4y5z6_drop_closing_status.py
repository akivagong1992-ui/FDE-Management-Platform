"""砍掉 project.status='closing' 状态：验收吸收其业务行为（已交付 / 触发 no_revenue 效益）

Revision ID: u1v2w3x4y5z6
Revises: t0u1v2w3x4y5
Create Date: 2026-05-29 18:00:00.000000

业务背景（2026-05-29 Akiva 拍板）：
- 状态机 5 → 4 个：drafting → in_progress → accepting → archived (+ cancelled)
- 收尾 (closing) 的所有业务依赖被验收 (accepting) 吸收：
  - 算"已交付"统计：原 (closing+archived) → 新 (accepting+archived)
  - 触发 no_revenue 项目效益金额：原 (closing+archived) → 新 (accepting+archived)
  - 算"按时交付率"分子：原 (closing+archived) → 新 (accepting+archived)
  - "在管"仅排除 archived/cancelled（验收仍在管）

数据迁移：现有 status='closing' → 'accepting'。
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'u1v2w3x4y5z6'
down_revision: Union[str, None] = 't0u1v2w3x4y5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE projects SET status = 'accepting' WHERE status = 'closing'")


def downgrade() -> None:
    # 无法精确还原（合并后丢失原始 closing 信息）。
    # 这里不动数据，仅作 placeholder。
    pass
