"""initial_schema

Revision ID: 89d82b9931f0
Revises:
Create Date: 2026-05-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "89d82b9931f0"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("api_key", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("api_key"),
    )

    op.create_table(
        "domains",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verification_method", sa.String(50), nullable=True),
        sa.Column("verification_token", sa.String(255), nullable=True),
        sa.Column("wts", sa.Float(), nullable=True),
        sa.Column("dr", sa.Float(), nullable=True),
        sa.Column("da", sa.Float(), nullable=True),
        sa.Column("spam_score", sa.Float(), nullable=True),
        sa.Column("domain_age_days", sa.Integer(), nullable=True),
        sa.Column("organic_traffic", sa.Integer(), nullable=True),
        sa.Column("content_quality", sa.Float(), nullable=True),
        sa.Column("is_pbn", sa.Boolean(), nullable=True),
        sa.Column("vetted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vetting_status", sa.String(50), nullable=True, server_default="pending"),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("niche", sa.String(100), nullable=True),
        sa.Column("language", sa.String(10), nullable=True, server_default="en"),
        sa.Column("blocklist", postgresql.JSON(), nullable=True),
        sa.Column("niche_strict", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("domain"),
    )
    op.create_index("idx_domains_user", "domains", ["user_id"])
    op.create_index("idx_domains_niche", "domains", ["niche"])
    op.create_index("idx_domains_wts", "domains", ["wts"])

    op.create_table(
        "pages",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("domain_id", sa.UUID(), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("niche", sa.String(100), nullable=True),
        sa.Column("language", sa.String(10), nullable=True, server_default="en"),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("embedding_id", sa.String(255), nullable=True),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_pages_domain", "pages", ["domain_id"])
    op.create_index("idx_pages_url", "pages", ["url"])

    op.create_table(
        "triangles",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("domain_a_id", sa.UUID(), nullable=False),
        sa.Column("domain_b_id", sa.UUID(), nullable=False),
        sa.Column("domain_c_id", sa.UUID(), nullable=False),
        sa.Column("link_ab_id", sa.UUID(), nullable=True),
        sa.Column("link_bc_id", sa.UUID(), nullable=True),
        sa.Column("link_ca_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="forming"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["domain_a_id"], ["domains.id"]),
        sa.ForeignKeyConstraint(["domain_b_id"], ["domains.id"]),
        sa.ForeignKeyConstraint(["domain_c_id"], ["domains.id"]),
    )

    op.create_table(
        "links",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("source_page_id", sa.UUID(), nullable=False),
        sa.Column("target_page_id", sa.UUID(), nullable=False),
        sa.Column("source_domain_id", sa.UUID(), nullable=False),
        sa.Column("target_domain_id", sa.UUID(), nullable=False),
        sa.Column("anchor_text", sa.String(512), nullable=False),
        sa.Column("match_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("match_breakdown", postgresql.JSON(), nullable=True),
        sa.Column("placement_type", sa.String(50), nullable=False, server_default="body"),
        sa.Column("credits_earned", sa.Numeric(12, 2), nullable=True),
        sa.Column("credits_spent", sa.Numeric(12, 2), nullable=True),
        sa.Column("triangle_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("placed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["source_page_id"], ["pages.id"]),
        sa.ForeignKeyConstraint(["target_page_id"], ["pages.id"]),
        sa.ForeignKeyConstraint(["source_domain_id"], ["domains.id"]),
        sa.ForeignKeyConstraint(["target_domain_id"], ["domains.id"]),
        sa.ForeignKeyConstraint(["triangle_id"], ["triangles.id"]),
    )
    op.create_index("idx_links_source_domain", "links", ["source_domain_id"])
    op.create_index("idx_links_target_domain", "links", ["target_domain_id"])
    op.create_index("idx_links_status", "links", ["status"])
    op.create_index("idx_links_triangle", "links", ["triangle_id"])

    op.create_foreign_key("fk_triangles_link_ab", "triangles", "links", ["link_ab_id"], ["id"])
    op.create_foreign_key("fk_triangles_link_bc", "triangles", "links", ["link_bc_id"], ["id"])
    op.create_foreign_key("fk_triangles_link_ca", "triangles", "links", ["link_ca_id"], ["id"])

    op.create_table(
        "credit_accounts",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("domain_id", sa.UUID(), nullable=False),
        sa.Column("balance", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("lifetime_earned", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("lifetime_spent", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("domain_id"),
    )

    op.create_table(
        "credit_transactions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("link_id", sa.UUID(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["account_id"], ["credit_accounts.id"]),
        sa.ForeignKeyConstraint(["link_id"], ["links.id"]),
    )
    op.create_index("idx_credit_tx_account", "credit_transactions", ["account_id"])
    op.create_index("idx_credit_tx_created", "credit_transactions", ["created_at"])

    op.create_table(
        "webhooks",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("events", postgresql.JSON(), nullable=False),
        sa.Column("secret", sa.String(255), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "domain_metrics_history",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("domain_id", sa.UUID(), nullable=False),
        sa.Column("dr", sa.Integer(), nullable=True),
        sa.Column("da", sa.Integer(), nullable=True),
        sa.Column("wts", sa.Integer(), nullable=True),
        sa.Column("organic_traffic", sa.Integer(), nullable=True),
        sa.Column("spam_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_metrics_domain_date", "domain_metrics_history", ["domain_id", "recorded_at"])


def downgrade() -> None:
    op.drop_table("domain_metrics_history")
    op.drop_table("webhooks")
    op.drop_table("credit_transactions")
    op.drop_table("credit_accounts")
    op.drop_constraint("fk_triangles_link_ab", "triangles", type_="foreignkey")
    op.drop_constraint("fk_triangles_link_bc", "triangles", type_="foreignkey")
    op.drop_constraint("fk_triangles_link_ca", "triangles", type_="foreignkey")
    op.drop_table("links")
    op.drop_table("triangles")
    op.drop_table("pages")
    op.drop_table("domains")
    op.drop_table("users")
