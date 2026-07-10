"""
app/api/v1/organizations.py — Organization API Controller
"""
import uuid
from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.orm import Session
from app.api.deps import (
    get_db,
    get_current_user,
    get_current_org_membership,
    require_owner,
    require_admin,
    require_member,
)
from app.models.user import User
from app.models.membership import Membership, Role
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
)
from app.schemas.membership import MembershipResponse
from app.schemas.invitation import (
    InvitationCreate,
    InvitationAccept,
    InvitationResponse,
)
from app.services.organization_service import organization_service
from app.repositories.organization_repository import organization_repository
from app.repositories.membership_repository import membership_repository
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from pydantic import BaseModel

router = APIRouter()


class SwitchOrgRequest(BaseModel):
    organization_id: uuid.UUID


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
)
def create_org(
    org_in: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new organization. The creator automatically becomes the OWNER.
    """
    return organization_service.create_organization(
        db,
        name=org_in.name,
        slug=org_in.slug,
        creator_id=current_user.id,
        description=org_in.description,
        logo_url=org_in.logo_url,
    )


@router.get(
    "",
    response_model=list[OrganizationResponse],
    summary="List user's organizations",
)
def list_orgs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all active organizations the authenticated user belongs to.
    """
    return organization_repository.get_all_for_user(db, user_id=current_user.id)


@router.get(
    "/{id}",
    response_model=OrganizationResponse,
    summary="Get organization details",
)
def get_org(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get organization details. User must be a member.
    """
    # Organization Isolation check: verify user membership
    membership = membership_repository.get_by_user_and_org(
        db, user_id=current_user.id, org_id=id
    )
    if not membership:
        raise NotFoundException("Organization not found")  # Return 404 to prevent enumeration
    
    org = organization_repository.get_by_id(db, org_id=id)
    if not org:
        raise NotFoundException("Organization not found")
    return org


@router.patch(
    "/{id}",
    response_model=OrganizationResponse,
    summary="Update organization details",
)
def update_org(
    id: uuid.UUID,
    org_in: OrganizationUpdate,
    membership: Membership = Depends(require_admin), # Requires ADMIN or higher
    db: Session = Depends(get_db),
):
    """
    Update organization details. Requires ADMIN or OWNER role.
    """
    # The require_admin dependency validates membership and role for the X-Organization-Id header.
    # However, we must ensure the route path ID matches the header ID to prevent cross-organization modification.
    if membership.organization_id != id:
        raise ForbiddenException("Route parameter ID does not match header Organization ID")

    return organization_service.update_organization(
        db,
        org_id=id,
        name=org_in.name,
        description=org_in.description,
        logo_url=org_in.logo_url,
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete an organization",
)
def delete_org(
    id: uuid.UUID,
    membership: Membership = Depends(require_owner), # Requires OWNER role
    db: Session = Depends(get_db),
):
    """
    Soft-delete an organization. Requires OWNER role.
    """
    if membership.organization_id != id:
        raise ForbiddenException("Route parameter ID does not match header Organization ID")

    organization_service.soft_delete_organization(db, org_id=id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{id}/invite",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a new member",
)
def invite_member(
    id: uuid.UUID,
    invite_in: InvitationCreate,
    membership: Membership = Depends(require_admin), # Requires ADMIN or higher
    db: Session = Depends(get_db),
):
    """
    Invite a user to the organization. Requires ADMIN or OWNER.
    """
    if membership.organization_id != id:
        raise ForbiddenException("Route parameter ID does not match header Organization ID")

    return organization_service.invite_member(
        db,
        org_id=id,
        email=invite_in.email,
        role=invite_in.role,
    )


@router.post(
    "/invitations/accept",
    response_model=MembershipResponse,
    summary="Accept an invitation",
)
def accept_invitation(
    accept_in: InvitationAccept,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Accept an invitation using the secure token.
    """
    return organization_service.accept_invitation(
        db,
        token=accept_in.token,
        user_id=current_user.id,
    )


@router.get(
    "/{id}/members",
    response_model=list[MembershipResponse],
    summary="List organization members",
)
def list_members(
    id: uuid.UUID,
    membership: Membership = Depends(require_member), # Requires MEMBER or higher
    db: Session = Depends(get_db),
):
    """
    List all members in the organization. Requires MEMBER or higher.
    """
    if membership.organization_id != id:
        raise ForbiddenException("Route parameter ID does not match header Organization ID")

    return membership_repository.get_members_by_org(db, org_id=id)


@router.delete(
    "/{id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member",
)
def remove_member(
    id: uuid.UUID,
    user_id: uuid.UUID,
    membership: Membership = Depends(require_admin), # Requires ADMIN or higher
    db: Session = Depends(get_db),
):
    """
    Remove a member from the organization. Requires ADMIN or OWNER.
    """
    if membership.organization_id != id:
        raise ForbiddenException("Route parameter ID does not match header Organization ID")

    # Prevent privilege escalation: non-owners cannot remove owners
    target_membership = membership_repository.get_by_user_and_org(db, user_id=user_id, org_id=id)
    if target_membership and target_membership.role == Role.OWNER and membership.role != Role.OWNER:
        raise ForbiddenException("Only owners can remove other owners")

    organization_service.remove_member(
        db,
        org_id=id,
        target_user_id=user_id,
        actor_id=membership.user_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/switch",
    summary="Switch active organization context",
)
def switch_organization(
    req: SwitchOrgRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Switch active organization. Validates that the user has a membership.
    """
    membership = membership_repository.get_by_user_and_org(
        db, user_id=current_user.id, org_id=req.organization_id
    )
    if not membership:
        raise ForbiddenException("You are not a member of this organization")

    # In a session-based or header-based architecture, the frontend uses the ID returned
    # here to set the X-Organization-Id header for future requests.
    return {"status": "success", "active_organization_id": str(req.organization_id)}


@router.get(
    "/current",
    response_model=OrganizationResponse,
    summary="Get current active organization",
)
def get_current_org(
    membership: Membership = Depends(require_member), # Validates active org header membership
    db: Session = Depends(get_db),
):
    """
    Get organization details of the current active context (from X-Organization-Id header).
    """
    org = organization_repository.get_by_id(db, org_id=membership.organization_id)
    if not org:
        raise NotFoundException("Organization not found")
    return org


@router.post(
    "/leave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave the organization",
)
def leave_org(
    membership: Membership = Depends(require_member), # From X-Organization-Id header
    db: Session = Depends(get_db),
):
    """
    Leave the active organization.
    """
    organization_service.leave_organization(
        db,
        org_id=membership.organization_id,
        user_id=membership.user_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
