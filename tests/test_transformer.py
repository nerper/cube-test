"""Unit tests for the transformer service."""

import pytest

from app.models import TransformCache
from app.services.transformer import transform_string, transform_strings


@pytest.mark.asyncio
async def test_transform_string_uppercase(db_session):
    """Test that transformer converts strings to uppercase."""
    result, cached = await transform_string(db_session, "hello world")

    assert result == "HELLO WORLD"
    assert cached is False  # First call should not be cached


@pytest.mark.asyncio
async def test_transform_string_caching(db_session):
    """Test that repeated transformations use cache."""
    # First call - should not be cached
    result1, cached1 = await transform_string(db_session, "test string")
    assert result1 == "TEST STRING"
    assert cached1 is False

    # Second call with same input - should be cached
    result2, cached2 = await transform_string(db_session, "test string")
    assert result2 == "TEST STRING"
    assert cached2 is True


@pytest.mark.asyncio
async def test_transform_string_stores_in_db(db_session):
    """Test that transformations are stored in the database."""
    await transform_string(db_session, "store me")
    await db_session.commit()

    # Query the cache table directly
    from sqlalchemy import select

    stmt = select(TransformCache).where(TransformCache.input_string == "store me")
    result = await db_session.execute(stmt)
    cached = result.scalar_one()

    assert cached.input_string == "store me"
    assert cached.transformed_string == "STORE ME"


@pytest.mark.asyncio
async def test_transform_strings_multiple(db_session):
    """Test transforming multiple strings at once."""
    inputs = ["one", "two", "three"]
    results, cache_hits = await transform_strings(db_session, inputs)

    assert results == ["ONE", "TWO", "THREE"]
    assert cache_hits == 0  # All are new


@pytest.mark.asyncio
async def test_transform_strings_partial_cache(db_session):
    """Test that partial cache hits work correctly."""
    # Pre-cache one string
    await transform_string(db_session, "cached")
    await db_session.commit()

    # Transform mix of cached and new strings
    inputs = ["cached", "new", "cached"]
    results, cache_hits = await transform_strings(db_session, inputs)

    assert results == ["CACHED", "NEW", "CACHED"]
    assert cache_hits == 2  # "cached" appears twice


@pytest.mark.asyncio
async def test_transform_empty_string(db_session):
    """Test that empty strings are handled correctly."""
    result, cached = await transform_string(db_session, "")

    assert result == ""
    assert cached is False


@pytest.mark.asyncio
async def test_transform_special_characters(db_session):
    """Test that special characters are preserved."""
    result, _ = await transform_string(db_session, "hello, world! 123")

    assert result == "HELLO, WORLD! 123"

