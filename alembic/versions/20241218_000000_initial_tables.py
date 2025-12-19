"""Initial tables for caching service.

Revision ID: 001
Revises: 
Create Date: 2024-12-18 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create transform_cache table
    op.create_table(
        "transform_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("input_string", sa.Text(), nullable=False),
        sa.Column("transformed_string", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_transform_cache_input_string",
        "transform_cache",
        ["input_string"],
        unique=True,
    )

    # Create payloads table
    op.create_table(
        "payloads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("list1_json", sa.Text(), nullable=False),
        sa.Column("list2_json", sa.Text(), nullable=False),
        sa.Column("output", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payloads_input_hash", "payloads", ["input_hash"], unique=True)
    op.create_index("ix_payloads_created_at", "payloads", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_payloads_created_at", table_name="payloads")
    op.drop_index("ix_payloads_input_hash", table_name="payloads")
    op.drop_table("payloads")
    op.drop_index("ix_transform_cache_input_string", table_name="transform_cache")
    op.drop_table("transform_cache")

