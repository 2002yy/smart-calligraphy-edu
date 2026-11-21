"""Track the authoritative attempt for each evaluation.

Revision ID: c71d8a9f0042
Revises: 8e1c2a3d4b5f
"""

from alembic import op
import sqlalchemy as sa


revision = "c71d8a9f0042"
down_revision = "8e1c2a3d4b5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Legacy finished scores retain NULL. A previous request must never be
    # granted authority merely because its row lacks a token.
    op.add_column(
        "evaluations", sa.Column("attempt_id", sa.String(length=32), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("evaluations", "attempt_id")
