"""Enforce one authoritative evaluation row per homework.

Revision ID: d8e42ac09311
Revises: c71d8a9f0042
"""

from alembic import op
import sqlalchemy as sa


revision = "d8e42ac09311"
down_revision = "c71d8a9f0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Do not silently delete historical evaluations to satisfy the index.
    duplicates = op.get_bind().execute(
        sa.text(
            "SELECT homework_id, COUNT(*) AS n FROM evaluations "
            "GROUP BY homework_id HAVING COUNT(*) > 1 LIMIT 1"
        )
    ).first()
    if duplicates:
        raise RuntimeError(
            "evaluations contains multiple rows for homework_id="
            f"{duplicates[0]}; reconcile historical records before creating "
            "uq_evaluations_homework_id. No rows have been removed."
        )
    op.create_index(
        "uq_evaluations_homework_id", "evaluations", ["homework_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("uq_evaluations_homework_id", table_name="evaluations")
