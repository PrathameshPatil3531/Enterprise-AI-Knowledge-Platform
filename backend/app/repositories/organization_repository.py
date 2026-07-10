"""
app/repositories/organization_repository.py — Organization Data Access Layer
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.organization import Organization


class OrganizationRepository:
    def get_by_id(self, db: Session, *, org_id: uuid.UUID) -> Organization | None:
        """Fetch active organization by ID (deleted_at is None)."""
        return (
            db.query(Organization)
            .filter(Organization.id == org_id, Organization.deleted_at.is_(None))
            .first()
        )

    def get_by_slug(self, db: Session, *, slug: str) -> Organization | None:
        """Fetch active organization by slug."""
        return (
            db.query(Organization)
            .filter(Organization.slug == slug.lower().strip(), Organization.deleted_at.is_(None))
            .first()
        )

    def get_all_for_user(self, db: Session, *, user_id: uuid.UUID) -> list[Organization]:
        """Fetch all active organizations a user belongs to."""
        from app.models.membership import Membership
        return (
            db.query(Organization)
            .join(Membership, Membership.organization_id == Organization.id)
            .filter(
                Membership.user_id == user_id,
                Organization.deleted_at.is_(None)
            )
            .all()
        )

    def create(
        self,
        db: Session,
        *,
        name: str,
        slug: str,
        description: str | None = None,
        logo_url: str | None = None,
    ) -> Organization:
        org = Organization(
            name=name,
            slug=slug.lower().strip(),
            description=description,
            logo_url=logo_url,
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        return org

    def update(
        self,
        db: Session,
        *,
        org: Organization,
        name: str | None = None,
        description: str | None = None,
        logo_url: str | None = None,
    ) -> Organization:
        if name is not None:
            org.name = name
        if description is not None:
            org.description = description
        if logo_url is not None:
            org.logo_url = logo_url
        db.commit()
        db.refresh(org)
        return org

    def soft_delete(self, db: Session, *, org: Organization) -> None:
        org.deleted_at = datetime.now(timezone.utc)
        db.commit()


organization_repository = OrganizationRepository()
