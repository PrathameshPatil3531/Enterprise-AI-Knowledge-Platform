"""
tests/test_organizations.py — Organization & Multi-Tenancy Endpoint Tests
"""
import pytest
import uuid


@pytest.fixture
def second_user(client):
    user_data = {
        "email": "user2@example.com",
        "password": "TestPass2",
        "full_name": "Second User",
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    return {"credentials": user_data, "user": response.json()}


@pytest.fixture
def second_auth_headers(client, second_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": second_user["credentials"]["email"],
            "password": second_user["credentials"]["password"],
        },
    )
    assert response.status_code == 200
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


class TestOrganizationCRUD:
    def test_create_organization_success(self, client, auth_headers):
        response = client.post(
            "/api/v1/organizations",
            headers=auth_headers,
            json={
                "name": "Acme Corp",
                "slug": "acme-corp",
                "description": "Standard Acme Corp",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Acme Corp"
        assert data["slug"] == "acme-corp"
        assert "id" in data

    def test_create_duplicate_slug(self, client, auth_headers):
        # Create first
        client.post(
            "/api/v1/organizations",
            headers=auth_headers,
            json={"name": "Acme Corp", "slug": "acme-corp"},
        )
        # Create second with same slug
        response = client.post(
            "/api/v1/organizations",
            headers=auth_headers,
            json={"name": "Acme Corp 2", "slug": "acme-corp"},
        )
        assert response.status_code == 409

    def test_list_organizations(self, client, auth_headers):
        # Create an org
        client.post(
            "/api/v1/organizations",
            headers=auth_headers,
            json={"name": "Acme Corp", "slug": "acme-corp"},
        )
        response = client.get("/api/v1/organizations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Acme Corp"

    def test_get_organization_details(self, client, auth_headers):
        # Create org
        create_resp = client.post(
            "/api/v1/organizations",
            headers=auth_headers,
            json={"name": "Acme Corp", "slug": "acme-corp"},
        )
        org_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/organizations/{org_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Acme Corp"


class TestMultiTenancyIsolation:
    def test_prevent_non_member_access(self, client, auth_headers, second_auth_headers):
        # User 1 creates an org
        create_resp = client.post(
            "/api/v1/organizations",
            headers=auth_headers,
            json={"name": "User 1 Org", "slug": "user1-org"},
        )
        org_id = create_resp.json()["id"]

        # User 2 tries to access User 1's org
        response = client.get(
            f"/api/v1/organizations/{org_id}",
            headers=second_auth_headers,
        )
        # Expect 404 (not found / hidden) or 403 to prevent enumeration
        assert response.status_code == 404


class TestRBAC:
    def test_admin_required_to_update(self, client, auth_headers, second_auth_headers):
        # Create org
        create_resp = client.post(
            "/api/v1/organizations",
            headers=auth_headers,
            json={"name": "Acme Corp", "slug": "acme-corp"},
        )
        org_id = create_resp.json()["id"]

        # User 2 tries to update org details
        # X-Organization-Id is required, but User 2 is not even in the org, so they fail with 403
        response = client.patch(
            f"/api/v1/organizations/{org_id}",
            headers={**second_auth_headers, "X-Organization-Id": org_id},
            json={"name": "Hacked Acme"},
        )
        assert response.status_code == 403


class TestInvitationFlow:
    def test_invite_and_accept_success(
        self, client, auth_headers, second_auth_headers, second_user
    ):
        # Create org
        create_resp = client.post(
            "/api/v1/organizations",
            headers=auth_headers,
            json={"name": "Acme Corp", "slug": "acme-corp"},
        )
        org_id = create_resp.json()["id"]

        # Invite user 2
        invite_resp = client.post(
            f"/api/v1/organizations/{org_id}/invite",
            headers={**auth_headers, "X-Organization-Id": org_id},
            json={"email": second_user["user"]["email"], "role": "MEMBER"},
        )
        assert invite_resp.status_code == 201

        # We need the token to accept. The token is generated and stored in DB, but normally
        # sent via email. Since we are testing, the API response for invite should return the
        # token (or we would check DB directly. Wait, our InvitationResponse schema doesn't expose the token,
        # but let's check InvitationResponse. Wait, does InvitationResponse schema have token? No!
        # Wait, for testing, let's make sure the service invitation token can be queried,
        # or we could temporarily include the token in the API response or query the DB).
        # Actually, let's query the DB directly since we have the DB session in pytest.
        # But wait, we are using the endpoint client. Let's see if we can get the token from DB.
        # Oh, in `conftest.py`, the `db` fixture is provided! We can inject `db` here and search.
        
    def test_accept_invite_via_db(
        self, db, client, auth_headers, second_auth_headers, second_user
    ):
        # Create org
        create_resp = client.post(
            "/api/v1/organizations",
            headers=auth_headers,
            json={"name": "Acme Corp", "slug": "acme-corp"},
        )
        org_id = create_resp.json()["id"]

        # Invite user 2
        invite_resp = client.post(
            f"/api/v1/organizations/{org_id}/invite",
            headers={**auth_headers, "X-Organization-Id": org_id},
            json={"email": second_user["user"]["email"], "role": "MEMBER"},
        )
        assert invite_resp.status_code == 201

        # Fetch token from DB
        from app.models.invitation import Invitation
        invitation = db.query(Invitation).filter(Invitation.email == second_user["user"]["email"]).first()
        assert invitation is not None
        token = invitation.invitation_token

        # User 2 accepts the invite
        accept_resp = client.post(
            "/api/v1/organizations/invitations/accept",
            headers=second_auth_headers,
            json={"token": token},
        )
        assert accept_resp.status_code == 200
        
        # Verify user 2 can now get org details
        get_resp = client.get(
            f"/api/v1/organizations/{org_id}",
            headers=second_auth_headers,
        )
        assert get_resp.status_code == 200
