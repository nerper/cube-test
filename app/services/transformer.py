"""
Transformer service that simulates an external transformation API.

The transformer converts strings to uppercase, simulating an external service
with artificial latency. Results are cached to avoid redundant transformations.
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import TransformCache


async def _simulate_external_transform(value: str) -> str:
    """
    Simulate an external transformation service.
    
    In a real scenario, this would be an HTTP call to an external API.
    We add artificial delay to demonstrate the benefit of caching.
    """
    await asyncio.sleep(settings.transformer_delay)
    return value.upper()


async def transform_string(db: AsyncSession, value: str) -> tuple[str, bool]:
    """
    Transform a string, using cache when available.
    
    Args:
        db: Database session for cache operations
        value: The string to transform
        
    Returns:
        Tuple of (transformed_string, was_cached)
    """
    # Check cache first
    stmt = select(TransformCache).where(TransformCache.input_string == value)
    result = await db.execute(stmt)
    cached = result.scalar_one_or_none()

    if cached is not None:
        return cached.transformed_string, True

    # Cache miss - call the transformer and store result
    transformed = await _simulate_external_transform(value)

    cache_entry = TransformCache(
        input_string=value,
        transformed_string=transformed,
    )
    db.add(cache_entry)
    await db.flush()  # Ensure it's written before returning

    return transformed, False


async def transform_strings(
    db: AsyncSession, values: list[str]
) -> tuple[list[str], int]:
    """
    Transform multiple strings, using cache when available.
    
    Args:
        db: Database session for cache operations
        values: List of strings to transform
        
    Returns:
        Tuple of (list of transformed strings, count of cache hits)
    """
    results: list[str] = []
    cache_hits = 0

    for value in values:
        transformed, was_cached = await transform_string(db, value)
        results.append(transformed)
        if was_cached:
            cache_hits += 1

    return results, cache_hits

