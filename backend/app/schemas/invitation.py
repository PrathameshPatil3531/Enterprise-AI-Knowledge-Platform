"""
app/schemas/invitation.py — Invitation Pydantic Schemas (DTOs)
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.models.invitation import InvitationStatus
from app.models.membership import Role


class InvitationCreate(BaseModel):
    email: EmailStr
    role: Role = Field(default=Role.MEMBER, description="The role the user will get upon accepting the invite.")


class InvitationAccept(BaseModel):
    token: str = Field(..., description="The cryptographically secure token sent via email.")


class InvitationResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    email: EmailStr
    status: InvitationStatus
    created_at: datetime
    expires_at: datetime
    accepted_at: datetime | None

    model_config = {"from_attributes": True}
