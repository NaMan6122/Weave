"""add_page_embeddings

Revision ID: b3f7a1c2e4d5
Revises: 89d82b9931f0
Create Date: 2026-05-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "b3f7a1c2e4d5"
down_revision: Union[str, None] = "89d82b9931f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("pages", sa.Column("embedding", Vector(384), nullable=True))
    op.create_index(
        "idx_pages_embedding",
        "pages",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("idx_pages_embedding")
    op.drop_column("pages", "embedding")
