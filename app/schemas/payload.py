"""Pydantic schemas for payload API requests and responses."""

from pydantic import BaseModel, Field, model_validator


class PayloadCreateRequest(BaseModel):
    """Request schema for creating a new payload."""

    list1: list[str] = Field(..., min_length=1, description="First list of strings")
    list2: list[str] = Field(..., min_length=1, description="Second list of strings")

    @model_validator(mode="after")
    def validate_equal_length(self) -> "PayloadCreateRequest":
        """Ensure both lists have the same length."""
        if len(self.list1) != len(self.list2):
            raise ValueError("list1 and list2 must have the same length")
        return self


class PayloadCreateResponse(BaseModel):
    """Response schema for payload creation."""

    id: str = Field(..., description="Unique identifier of the created payload")
    cached: bool = Field(
        ..., description="Whether the payload was retrieved from cache"
    )


class PayloadGetResponse(BaseModel):
    """Response schema for retrieving a payload."""

    output: str = Field(..., description="The generated interleaved output string")

