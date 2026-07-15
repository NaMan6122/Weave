"""rename_stripe_to_dodo_customer_id

Revision ID: c5d9e4f6a7b8
Revises: b3f7a1c2e4d5
Create Date: 2026-07-15
"""

from typing import Sequence, Union

from alembic import op

revision: str = "c5d9e4f6a7b8"
down_revision: Union[str, None] = "b3f7a1c2e4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users", "stripe_customer_id",
        new_column_name="dodo_customer_id",
    )


def downgrade() -> None:
    op.alter_column(
        "users", "dodo_customer_id",
        new_column_name="stripe_customer_id",
    )