"""
app/schemas/organization.py — Organization Pydantic Schemas (DTOs)
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the organization.")
    description: str | None = Field(None, max_length=1000, description="Optional description.")
    logo_url: str | None = Field(None, max_length=1024, description="Optional logo URL.")


class OrganizationCreate(OrganizationBase):
    slug: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="URL-friendly unique identifier (slug). Must be lowercase, alphanumeric, and hyphens only."
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.lower().strip()
        if not re.match(r"^[a-z0-9\-]+$", v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens.")
        if v.startswith("-") or v.endswith("-"):
            raise ValueError("Slug cannot start or end with a hyphen.")
        return v


class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    logo_url: str | None = Field(None, max_length=1024)


class OrganizationResponse(OrganizationBase):
    id: uuid.UUID
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
