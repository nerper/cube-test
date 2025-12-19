"""Integration tests for the API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test the health check endpoint."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_create_payload_success(client: AsyncClient):
    """Test successful payload creation."""
    response = await client.post(
        "/payload",
        json={
            "list1": ["hello", "world"],
            "list2": ["foo", "bar"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["cached"] is False

    # Verify it's a valid SHA-256 hash (64 hex characters)
    assert len(data["id"]) == 64
    assert all(c in "0123456789abcdef" for c in data["id"])


@pytest.mark.asyncio
async def test_create_payload_sample_input(client: AsyncClient):
    """Test the sample input from requirements."""
    response = await client.post(
        "/payload",
        json={
            "list1": ["first string", "second string", "third string"],
            "list2": ["other string", "another string", "last string"],
        },
    )

    assert response.status_code == 201
    payload_id = response.json()["id"]

    # Retrieve the payload
    get_response = await client.get(f"/payload/{payload_id}")
    assert get_response.status_code == 200

    expected = "FIRST STRING, OTHER STRING, SECOND STRING, ANOTHER STRING, THIRD STRING, LAST STRING"
    assert get_response.json()["output"] == expected


@pytest.mark.asyncio
async def test_create_payload_deduplication(client: AsyncClient):
    """Test that identical inputs return the same payload ID."""
    payload = {
        "list1": ["test"],
        "list2": ["test"],
    }

    # First request
    response1 = await client.post("/payload", json=payload)
    assert response1.status_code == 201
    data1 = response1.json()
    assert data1["cached"] is False

    # Second request with same data
    response2 = await client.post("/payload", json=payload)
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["cached"] is True

    # Same ID returned
    assert data1["id"] == data2["id"]


@pytest.mark.asyncio
async def test_create_payload_validation_empty_list1(client: AsyncClient):
    """Test validation rejects empty list1."""
    response = await client.post(
        "/payload",
        json={
            "list1": [],
            "list2": ["test"],
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_payload_validation_empty_list2(client: AsyncClient):
    """Test validation rejects empty list2."""
    response = await client.post(
        "/payload",
        json={
            "list1": ["test"],
            "list2": [],
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_payload_validation_unequal_length(client: AsyncClient):
    """Test validation rejects lists of different lengths."""
    response = await client.post(
        "/payload",
        json={
            "list1": ["one", "two"],
            "list2": ["single"],
        },
    )

    assert response.status_code == 422
    assert "same length" in response.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_get_payload_success(client: AsyncClient):
    """Test successful payload retrieval."""
    # Create a payload first
    create_response = await client.post(
        "/payload",
        json={
            "list1": ["get", "test"],
            "list2": ["success", "here"],
        },
    )
    payload_id = create_response.json()["id"]

    # Retrieve it
    get_response = await client.get(f"/payload/{payload_id}")

    assert get_response.status_code == 200
    assert get_response.json()["output"] == "GET, SUCCESS, TEST, HERE"


@pytest.mark.asyncio
async def test_get_payload_not_found(client: AsyncClient):
    """Test 404 response for non-existent payload."""
    # Use a valid SHA-256 format string (64 hex chars) that doesn't exist
    fake_id = "a" * 64
    response = await client.get(f"/payload/{fake_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_payload_invalid_format(client: AsyncClient):
    """Test that invalid hash format still works (no validation, just 404 if not found)."""
    # Since we're using string IDs, FastAPI won't validate format
    # But a non-existent ID will return 404
    response = await client.get("/payload/not-a-valid-hash")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_payload_missing_fields(client: AsyncClient):
    """Test validation rejects missing required fields."""
    response = await client.post(
        "/payload",
        json={"list1": ["test"]},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_multiple_different_payloads(client: AsyncClient):
    """Test creating multiple different payloads."""
    # Create first payload
    response1 = await client.post(
        "/payload",
        json={
            "list1": ["a"],
            "list2": ["b"],
        },
    )
    id1 = response1.json()["id"]

    # Create second payload with different data
    response2 = await client.post(
        "/payload",
        json={
            "list1": ["x"],
            "list2": ["y"],
        },
    )
    id2 = response2.json()["id"]

    # IDs should be different
    assert id1 != id2

    # Both should be retrievable
    get1 = await client.get(f"/payload/{id1}")
    get2 = await client.get(f"/payload/{id2}")

    assert get1.json()["output"] == "A, B"
    assert get2.json()["output"] == "X, Y"

