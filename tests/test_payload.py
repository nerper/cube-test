"""Unit tests for the payload service."""

import pytest

from app.services.payload import (
    _compute_input_hash,
    _interleave_lists,
    create_payload,
    get_payload,
)


class TestInterleave:
    """Tests for the interleave helper function."""

    def test_interleave_basic(self):
        """Test basic interleaving of two lists."""
        result = _interleave_lists(["A", "B", "C"], ["X", "Y", "Z"])
        assert result == "A, X, B, Y, C, Z"

    def test_interleave_single_element(self):
        """Test interleaving single-element lists."""
        result = _interleave_lists(["ONE"], ["TWO"])
        assert result == "ONE, TWO"

    def test_interleave_with_spaces(self):
        """Test interleaving strings containing spaces."""
        result = _interleave_lists(["hello world"], ["foo bar"])
        assert result == "hello world, foo bar"


class TestInputHash:
    """Tests for the input hash computation."""

    def test_hash_deterministic(self):
        """Test that same inputs produce same hash."""
        hash1 = _compute_input_hash(["a", "b"], ["x", "y"])
        hash2 = _compute_input_hash(["a", "b"], ["x", "y"])
        assert hash1 == hash2

    def test_hash_different_inputs(self):
        """Test that different inputs produce different hashes."""
        hash1 = _compute_input_hash(["a", "b"], ["x", "y"])
        hash2 = _compute_input_hash(["a", "b"], ["x", "z"])
        assert hash1 != hash2

    def test_hash_order_matters(self):
        """Test that list order affects hash."""
        hash1 = _compute_input_hash(["a", "b"], ["x", "y"])
        hash2 = _compute_input_hash(["b", "a"], ["x", "y"])
        assert hash1 != hash2

    def test_hash_is_sha256(self):
        """Test that hash is 64 characters (SHA256 hex)."""
        result = _compute_input_hash(["test"], ["test"])
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)


@pytest.mark.asyncio
async def test_create_payload_basic(db_session):
    """Test basic payload creation."""
    list1 = ["first", "second"]
    list2 = ["third", "fourth"]

    payload_id, cached = await create_payload(db_session, list1, list2)
    await db_session.commit()

    assert payload_id is not None
    assert cached is False


@pytest.mark.asyncio
async def test_create_payload_interleaves_correctly(db_session):
    """Test that payload output is correctly interleaved."""
    list1 = ["one", "two"]
    list2 = ["three", "four"]

    payload_id, _ = await create_payload(db_session, list1, list2)
    await db_session.commit()

    payload = await get_payload(db_session, payload_id)
    assert payload is not None
    # Transformed to uppercase and interleaved
    assert payload.output == "ONE, THREE, TWO, FOUR"


@pytest.mark.asyncio
async def test_create_payload_deduplication(db_session):
    """Test that identical inputs return the same payload ID."""
    list1 = ["test"]
    list2 = ["test"]

    # Create first payload
    payload_id1, cached1 = await create_payload(db_session, list1, list2)
    await db_session.commit()
    assert cached1 is False

    # Create second payload with same inputs
    payload_id2, cached2 = await create_payload(db_session, list1, list2)
    await db_session.commit()
    assert cached2 is True

    # Should return same ID
    assert payload_id1 == payload_id2


@pytest.mark.asyncio
async def test_get_payload_not_found(db_session):
    """Test that getting non-existent payload returns None."""
    import uuid

    result = await get_payload(db_session, uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_create_payload_sample_input(db_session):
    """Test the sample input from the requirements."""
    list1 = ["first string", "second string", "third string"]
    list2 = ["other string", "another string", "last string"]

    payload_id, _ = await create_payload(db_session, list1, list2)
    await db_session.commit()

    payload = await get_payload(db_session, payload_id)
    assert payload is not None

    expected = "FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING, THIRD STRING, LAST STRING"
    assert payload.output == expected

