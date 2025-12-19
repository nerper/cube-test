"""
Payload service for generating and retrieving interleaved payloads.

Handles payload generation with deduplication - identical inputs return
the same payload ID instead of creating duplicates. Uses deterministic
SHA-256 hashes of inputs as payload IDs for true idempotency.
"""

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payload
from app.services.transformer import transform_strings


def _compute_input_hash(list1: list[str], list2: list[str]) -> str:
    """
    Compute a deterministic hash for the input lists.
    
    Uses canonical JSON serialization to ensure identical inputs
    always produce the same hash, enabling deduplication.
    """
    # Canonical representation: sorted keys, no extra whitespace
    canonical = json.dumps({"list1": list1, "list2": list2}, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _interleave_lists(list1: list[str], list2: list[str]) -> str:
    """
    Interleave two lists and join with commas.
    
    Example: [A, B, C] and [X, Y, Z] -> "A, X, B, Y, C, Z"
    """
    interleaved: list[str] = []
    for item1, item2 in zip(list1, list2):
        interleaved.extend([item1, item2])
    return ", ".join(interleaved)


async def create_payload(
    db: AsyncSession, list1: list[str], list2: list[str]
) -> tuple[str, bool]:
    """
    Create a new payload or return existing one if inputs match.
    
    Args:
        db: Database session
        list1: First list of strings
        list2: Second list of strings
        
    Returns:
        Tuple of (payload_id, was_cached) where payload_id is the deterministic
        SHA-256 hash of the inputs, and was_cached indicates if an existing
        payload was returned instead of creating new one
    """
    # Compute deterministic hash for the inputs
    input_hash = _compute_input_hash(list1, list2)
    
    # Check for existing payload with same inputs (using id which equals input_hash)
    stmt = select(Payload).where(Payload.id == input_hash)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing is not None:
        return existing.id, True

    # Transform all strings from both lists
    all_strings = list1 + list2
    transformed, _ = await transform_strings(db, all_strings)

    # Split back into two lists
    mid = len(list1)
    transformed_list1 = transformed[:mid]
    transformed_list2 = transformed[mid:]

    # Generate interleaved output
    output = _interleave_lists(transformed_list1, transformed_list2)

    # Store the new payload with deterministic ID
    payload = Payload(
        id=input_hash,
        input_hash=input_hash,
        list1_json=json.dumps(list1),
        list2_json=json.dumps(list2),
        output=output,
    )
    db.add(payload)
    await db.flush()

    return payload.id, False


async def get_payload(db: AsyncSession, payload_id: str) -> Payload | None:
    """
    Retrieve a payload by its ID.
    
    Args:
        db: Database session
        payload_id: SHA-256 hash string (64 chars) of the payload to retrieve
        
    Returns:
        Payload object if found, None otherwise
    """
    stmt = select(Payload).where(Payload.id == payload_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

