"""
app/schemas/membership.py — Membership Pydantic Schemas (DTOs)
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.membership import Role, MembershipStatus
from app.schemas.user import UserResponse


class MembershipBase(BaseModel):
    role: Role = Field(default=Role.MEMBER)
    status: MembershipStatus = Field(default=MembershipStatus.ACTIVE)


class MembershipUpdate(BaseModel):
    role: Role | None = None
    status: MembershipStatus | None = None


class MembershipResponse(MembershipBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    joined_at: datetime
    user: UserResponse | None = None

    model_config = {"from_attributes": True}
