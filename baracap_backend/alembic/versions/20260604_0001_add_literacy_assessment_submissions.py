"""add literacy assessment submissions

Revision ID: 20260604_0001
Revises:
Create Date: 2026-06-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from app.models import GUID


revision = "20260604_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "literacy_assessment_submissions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("first_name", sa.String(length=80), nullable=False),
        sa.Column("last_name", sa.String(length=80), nullable=False),
        sa.Column("phone", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(length=80), nullable=False),
        sa.Column("guide_type", sa.String(length=20), nullable=False),
        sa.Column("language", sa.String(length=2), server_default="uz", nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_literacy_assessment_submissions_created_at",
        "literacy_assessment_submissions",
        ["created_at"],
    )
    op.create_index(
        "ix_literacy_assessment_submissions_phone",
        "literacy_assessment_submissions",
        ["phone"],
    )
    op.create_index(
        "ix_literacy_assessment_submissions_score",
        "literacy_assessment_submissions",
        ["score"],
    )


def downgrade() -> None:
    op.drop_index("ix_literacy_assessment_submissions_score", table_name="literacy_assessment_submissions")
    op.drop_index("ix_literacy_assessment_submissions_phone", table_name="literacy_assessment_submissions")
    op.drop_index("ix_literacy_assessment_submissions_created_at", table_name="literacy_assessment_submissions")
    op.drop_table("literacy_assessment_submissions")
