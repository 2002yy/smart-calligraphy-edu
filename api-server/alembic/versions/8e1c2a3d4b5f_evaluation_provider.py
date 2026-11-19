"""Preserve evaluation provider provenance without guessing historical rows.

Revision ID: 8e1c2a3d4b5f
Revises: 07d4e0bf7e46
"""

from alembic import op
import sqlalchemy as sa


revision = "8e1c2a3d4b5f"
down_revision = "07d4e0bf7e46"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # NULL = 未知来源；历史 Mock 和真实评分无法仅靠现有字段区分。
    op.add_column("evaluations", sa.Column("provider", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("evaluations", "provider")
