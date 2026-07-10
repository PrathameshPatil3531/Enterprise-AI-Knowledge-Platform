"""
app/repositories/invitation_repository.py — Invitation Data Access Layer
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.invitation import Invitation, InvitationStatus


class InvitationRepository:
    def get_by_token(self, db: Session, *, token: str) -> Invitation | None:
        """Fetch invitation by its secure token."""
        return db.query(Invitation).filter(Invitation.invitation_token == token).first()

    def get_pending_by_email_and_org(
        self, db: Session, *, email: str, org_id: uuid.UUID
    ) -> Invitation | None:
        """Fetch pending invitation for email in an organization."""
        return (
            db.query(Invitation)
            .filter(
                Invitation.email == email.lower().strip(),
                Invitation.organization_id == org_id,
                Invitation.status == InvitationStatus.PENDING,
                Invitation.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )

    def create(
        self,
        db: Session,
        *,
        org_id: uuid.UUID,
        email: str,
        token: str,
        expires_at: datetime,
    ) -> Invitation:
        invitation = Invitation(
            organization_id=org_id,
            email=email.lower().strip(),
            invitation_token=token,
            expires_at=expires_at,
            status=InvitationStatus.PENDING,
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation

    def accept(self, db: Session, *, invitation: Invitation) -> None:
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.now(timezone.utc)
        db.commit()


invitation_repository = InvitationRepository()
