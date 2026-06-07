"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "app_user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("clerk_user_id", sa.String(255), nullable=False, unique=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_app_user_clerk_user_id", "app_user", ["clerk_user_id"])

    op.create_table(
        "user_api_key",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("key_ciphertext", sa.LargeBinary, nullable=False),
        sa.Column("key_nonce", sa.LargeBinary, nullable=False),
        sa.Column("key_fingerprint", sa.String(32), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )
    op.create_index("ix_user_api_key_user_id", "user_api_key", ["user_id"])

    op.create_table(
        "template",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_pptx_url", sa.Text, nullable=False),
        sa.Column("design_tokens", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("thumbnail_url", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_template_user_id", "template", ["user_id"])

    op.create_table(
        "project",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("topic", sa.Text, nullable=False),
        sa.Column("brief", sa.Text, nullable=True),
        sa.Column("language", sa.String(8), nullable=False, server_default="en"),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("template.id", ondelete="SET NULL"), nullable=True),
        sa.Column("default_settings", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_project_user_id", "project", ["user_id"])
    op.create_index("idx_project_user", "project", ["user_id", sa.text("updated_at DESC")])

    op.create_table(
        "deck",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("project.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("slide_count", sa.Integer, nullable=False, server_default="10"),
        sa.Column("blueprint", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("research_brief", postgresql.JSONB, nullable=True),
        sa.Column("generation_meta", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_deck_project_id", "deck", ["project_id"])
    op.create_index("idx_deck_project", "deck", ["project_id", sa.text("created_at DESC")])

    op.create_table(
        "deck_version",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("deck_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deck.id", ondelete="CASCADE"), nullable=False),
        sa.Column("blueprint", postgresql.JSONB, nullable=False),
        sa.Column("label", sa.String(64), nullable=True),
        sa.Column("author", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_deck_version_deck_id", "deck_version", ["deck_id"])

    op.create_table(
        "generation_job",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("deck_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deck.id", ondelete="CASCADE"), nullable=False),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("stage", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("progress_pct", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_generation_job_deck_id", "generation_job", ["deck_id"])

    op.create_table(
        "export_artifact",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("deck_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deck.id", ondelete="CASCADE"), nullable=False),
        sa.Column("format", sa.String(16), nullable=False, server_default="pptx"),
        sa.Column("storage_url", sa.Text, nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_export_artifact_deck_id", "export_artifact", ["deck_id"])


def downgrade() -> None:
    for t in (
        "export_artifact",
        "generation_job",
        "deck_version",
        "deck",
        "project",
        "template",
        "user_api_key",
        "app_user",
    ):
        op.drop_table(t)
