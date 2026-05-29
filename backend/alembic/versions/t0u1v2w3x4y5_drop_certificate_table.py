"""砍掉 Certificate 表 + EngineerSkillSnapshot.cert_count + EngineerSkill.level
（统一到 Skill 字典：等级是认证内禀属性，由 Skill.level 提供，工程师层不再带等级）。

Revision ID: t0u1v2w3x4y5
Revises: s9t0u1v2w3x4
Create Date: 2026-05-29 17:00:00.000000

业务背景（2026-05-29 Akiva 拍板，见 docs/CHAT-2026-05-29 决策讨论）：
- 用户不需要证书编号 / 颁发日 / 到期日 / 实物附件 → Certificate 表 4 个独有字段都是死代码
- 等级 L1-L3 是认证内禀难度（来自 Skill 字典），不是个人掌握度 → EngineerSkill.level
  本就该砍（migration a1b2c3d4 已经清空但保留列结构）
- 团队能力快照的 avg_level 改为来自 Skill.level 聚合，cert_count 不再需要
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 't0u1v2w3x4y5'
down_revision: Union[str, None] = 's9t0u1v2w3x4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) 砍 Certificate 表
    op.drop_table("certificates")

    # 2) 砍 EngineerSkillSnapshot.cert_count（migration a1b2c3d4 后已无意义）
    with op.batch_alter_table("engineer_skill_snapshots") as batch:
        batch.drop_column("cert_count")

    # 3) 砍 EngineerSkill.level（migration a1b2c3d4 已清 0，但列还在）
    with op.batch_alter_table("engineer_skills") as batch:
        batch.drop_column("level")


def downgrade() -> None:
    # 加回 EngineerSkill.level（默认 1，跟 a1b2c3d4 一致）
    with op.batch_alter_table("engineer_skills") as batch:
        batch.add_column(sa.Column("level", sa.Integer(), nullable=False, server_default="1"))

    # 加回 cert_count（默认 0）
    with op.batch_alter_table("engineer_skill_snapshots") as batch:
        batch.add_column(sa.Column("cert_count", sa.Integer(), nullable=False, server_default="0"))

    # 加回 Certificate 表
    op.create_table(
        "certificates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("engineer_id", sa.Integer(), sa.ForeignKey("engineers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("issuer", sa.String(length=128), nullable=True),
        sa.Column("cert_number", sa.String(length=128), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("file_path", sa.String(length=255), nullable=True),
        sa.Column("cert_level", sa.String(length=4), nullable=True),
        sa.Column("cert_category", sa.String(length=16), nullable=True),
    )
    op.create_index("ix_certificates_engineer_id", "certificates", ["engineer_id"])
