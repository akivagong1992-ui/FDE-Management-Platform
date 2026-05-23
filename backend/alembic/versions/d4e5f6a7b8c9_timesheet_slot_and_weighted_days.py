"""timesheet: slot booleans + is_workday + natural/weighted days

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-24 11:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("timesheets") as batch:
        batch.add_column(sa.Column("has_morning", sa.Boolean(),
                                   nullable=False, server_default=sa.text("0")))
        batch.add_column(sa.Column("has_afternoon", sa.Boolean(),
                                   nullable=False, server_default=sa.text("0")))
        batch.add_column(sa.Column("has_evening", sa.Boolean(),
                                   nullable=False, server_default=sa.text("0")))
        batch.add_column(sa.Column("is_workday", sa.Boolean(),
                                   nullable=False, server_default=sa.text("1")))
        batch.add_column(sa.Column("natural_days", sa.Numeric(4, 2),
                                   nullable=False, server_default="0"))
        batch.add_column(sa.Column("weighted_days", sa.Numeric(4, 2),
                                   nullable=False, server_default="0"))

    # 将旧 person_days 的语义迁移到 weighted_days（视作 1.0× 倍率历史值）
    # 同时按 person_days 大致还原 slot 选择（启发式）：
    # ≥1.5 → 整天+晚上、≥1.0 → 上下午、≥0.5 → 上午
    op.execute("""
        UPDATE timesheets SET
          weighted_days = COALESCE(person_days, 0),
          natural_days  = COALESCE(person_days, 0),
          has_morning   = CASE WHEN person_days >= 0.5 THEN 1 ELSE 0 END,
          has_afternoon = CASE WHEN person_days >= 1.0 THEN 1 ELSE 0 END,
          has_evening   = CASE WHEN person_days >= 1.5 THEN 1 ELSE 0 END,
          is_workday    = CASE
              WHEN strftime('%w', work_date) IN ('0', '6') THEN 0 ELSE 1
          END
        WHERE 1 = 1
    """)

    with op.batch_alter_table("timesheets") as batch:
        batch.drop_column("person_days")


def downgrade() -> None:
    with op.batch_alter_table("timesheets") as batch:
        batch.add_column(sa.Column("person_days", sa.Numeric(4, 1),
                                   nullable=True))
    op.execute("UPDATE timesheets SET person_days = weighted_days")
    with op.batch_alter_table("timesheets") as batch:
        batch.alter_column("person_days", nullable=False)
        batch.drop_column("weighted_days")
        batch.drop_column("natural_days")
        batch.drop_column("is_workday")
        batch.drop_column("has_evening")
        batch.drop_column("has_afternoon")
        batch.drop_column("has_morning")
