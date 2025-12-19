"""API routes for payload operations."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import PayloadCreateRequest, PayloadCreateResponse, PayloadGetResponse
from app.services import payload as payload_service

router = APIRouter(prefix="/payload", tags=["payload"])


@router.post(
    "",
    response_model=PayloadCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new payload",
    description="Generate a payload by transforming and interleaving two string lists. "
    "Returns the same ID if identical inputs were previously submitted.",
)
async def create_payload(
    request: PayloadCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> PayloadCreateResponse:
    """
    Create a new payload from two lists of strings.
    
    The strings are transformed (uppercase) and interleaved.
    If the exact same inputs were submitted before, the existing
    payload ID is returned instead of creating a duplicate.
    """
    payload_id, cached = await payload_service.create_payload(
        db, request.list1, request.list2
    )
    return PayloadCreateResponse(id=str(payload_id), cached=cached)


@router.get(
    "/{payload_id}",
    response_model=PayloadGetResponse,
    summary="Retrieve a payload",
    description="Get the generated output for a previously created payload.",
)
async def get_payload(
    payload_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PayloadGetResponse:
    """Retrieve a payload by its ID."""
    payload = await payload_service.get_payload(db, payload_id)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payload with ID {payload_id} not found",
        )

    return PayloadGetResponse(output=payload.output)

