"""add_notifications_table

Revision ID: d6e0f7a8b9c0
Revises: c5d9e4f6a7b8
Create Date: 2026-07-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "d6e0f7a8b9c0"
down_revision: Union[str, None] = "c5d9e4f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("read", sa.Boolean, nullable=False, default=False),
        sa.Column("metadata", JSONB, default=dict),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_notif_user_unread",
        "notifications",
        ["user_id", "read"],
        postgresql_where=sa.text("read = FALSE"),
    )
    op.create_index(
        "idx_notif_user_created",
        "notifications",
        ["user_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_notif_user_created", table_name="notifications")
    op.drop_index("idx_notif_user_unread", table_name="notifications")
    op.drop_table("notifications")
