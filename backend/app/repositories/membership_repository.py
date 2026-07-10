"""
app/repositories/membership_repository.py — Membership Data Access Layer
"""
import uuid
from sqlalchemy.orm import Session, joinedload
from app.models.membership import Membership, Role, MembershipStatus


class MembershipRepository:
    def get_by_user_and_org(
        self, db: Session, *, user_id: uuid.UUID, org_id: uuid.UUID
    ) -> Membership | None:
        """Fetch a membership record for a specific user and organization."""
        return (
            db.query(Membership)
            .filter(Membership.user_id == user_id, Membership.organization_id == org_id)
            .first()
        )

    def get_members_by_org(
        self, db: Session, *, org_id: uuid.UUID
    ) -> list[Membership]:
        """Fetch all membership records for an organization (eagerly loading User info)."""
        return (
            db.query(Membership)
            .options(joinedload(Membership.user))
            .filter(Membership.organization_id == org_id)
            .all()
        )

    def create(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        role: Role = Role.MEMBER,
        status: MembershipStatus = MembershipStatus.ACTIVE,
    ) -> Membership:
        membership = Membership(
            user_id=user_id,
            organization_id=org_id,
            role=role,
            status=status,
        )
        db.add(membership)
        db.commit()
        db.refresh(membership)
        return membership

    def update_role(
        self, db: Session, *, membership: Membership, role: Role
    ) -> Membership:
        membership.role = role
        db.commit()
        db.refresh(membership)
        return membership

    def update_status(
        self, db: Session, *, membership: Membership, status: MembershipStatus
    ) -> Membership:
        membership.status = status
        db.commit()
        db.refresh(membership)
        return membership

    def delete(self, db: Session, *, membership: Membership) -> None:
        db.delete(membership)
        db.commit()


membership_repository = MembershipRepository()
