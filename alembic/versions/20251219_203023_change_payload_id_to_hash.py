"""Change payload ID from UUID to deterministic SHA-256 hash.

Revision ID: 002
Revises: 001
Create Date: 2025-12-19 20:30:23.000000

"""
from typing import Sequence, Union

import hashlib
import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _compute_input_hash(list1: list[str], list2: list[str]) -> str:
    """Compute SHA-256 hash of normalized inputs."""
    canonical = json.dumps({"list1": list1, "list2": list2}, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def upgrade() -> None:
    # For existing records, we need to compute the hash from stored JSON
    # and update the id column. We'll:
    # 1. Add a temporary column for the new hash ID
    # 2. Compute hashes for existing records using Python
    # 3. Drop old id column and constraints
    # 4. Rename temp column to id and add constraints
    
    # Step 1: Add temporary column for new hash-based ID
    op.add_column(
        "payloads",
        sa.Column("id_hash", sa.String(64), nullable=True),
    )
    
    # Step 2: Compute hashes for existing records
    # Use op.get_bind() to get connection for data migration
    conn = op.get_bind()
    
    # Fetch all existing records
    result = conn.execute(
        sa.text("SELECT id::text, list1_json, list2_json FROM payloads")
    )
    records = result.fetchall()
    
    # Update each record with computed hash
    for old_id, list1_json, list2_json in records:
        list1 = json.loads(list1_json)
        list2 = json.loads(list2_json)
        new_id = _compute_input_hash(list1, list2)
        
        conn.execute(
            sa.text("UPDATE payloads SET id_hash = :new_id WHERE id::text = :old_id"),
            {"new_id": new_id, "old_id": old_id},
        )
    
    # Step 3: Drop old primary key constraint and id column
    op.drop_constraint("payloads_pkey", "payloads", type_="primary")
    op.drop_column("payloads", "id")
    
    # Step 4: Rename id_hash to id and make it primary key
    op.alter_column("payloads", "id_hash", new_column_name="id", nullable=False)
    op.create_primary_key("payloads_pkey", "payloads", ["id"])


def downgrade() -> None:
    # Reverse the migration: convert hash IDs back to UUIDs
    # This is lossy - we can't recover the original UUIDs, so we'll generate new ones
    
    # Add temporary UUID column
    op.add_column(
        "payloads",
        sa.Column("id_uuid", postgresql.UUID(as_uuid=True), nullable=True),
    )
    
    # Generate new UUIDs for all records
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM payloads"))
    records = result.fetchall()
    
    import uuid
    
    for (old_id,) in records:
        new_uuid = uuid.uuid4()
        connection.execute(
            sa.text("UPDATE payloads SET id_uuid = :new_uuid WHERE id = :old_id"),
            {"new_uuid": new_uuid, "old_id": old_id},
        )
    
    # Drop old primary key and id column
    op.drop_constraint("payloads_pkey", "payloads", type_="primary")
    op.drop_column("payloads", "id")
    
    # Rename id_uuid to id and make it primary key
    op.alter_column("payloads", "id_uuid", new_column_name="id", nullable=False)
    op.create_primary_key("payloads_pkey", "payloads", ["id"])

