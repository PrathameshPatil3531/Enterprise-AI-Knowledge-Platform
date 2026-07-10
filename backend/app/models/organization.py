"""
app/models/organization.py — Organization ORM Model

Organizations are the primary tenant isolation boundary in our system.
All resources (documents, chats, etc.) in the future MUST belong to an organization,
and queries must scope to `organization_id` to prevent cross-tenant data leaks.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.membership import Membership
    from app.models.invitation import Invitation


class Organization(Base):
    """
    Represents a tenant (Organization) in the system.
    Users belong to Organizations via the Membership table.
    """
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # URL-friendly unique identifier (e.g., 'acme-corp')
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    # Soft deletion: If set, the org is considered deleted and should be hidden from queries.
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    memberships: Mapped[List["Membership"]] = relationship(
        "Membership",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    
    invitations: Mapped[List["Invitation"]] = relationship(
        "Invitation",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Organization id={self.id!s:.8} name={self.name} slug={self.slug}>"
