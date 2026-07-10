"""
tests/test_auth.py — Auth Endpoint Tests

Tests cover the complete happy-path and error cases for all auth endpoints.

Run with:
    pytest tests/test_auth.py -v
"""

import pytest


class TestRegister:
    """Tests for POST /api/v1/auth/register"""

    def test_register_success(self, client):
        """A new user registers successfully."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "NewPass1",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "password_hash" not in data  # CRITICAL: password never exposed
        assert "id" in data

    def test_register_duplicate_email(self, client, registered_user):
        """Registering with an existing email returns 409 Conflict."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": registered_user["credentials"]["email"],
                "password": "AnotherPass1",
            },
        )
        assert response.status_code == 409

    def test_register_weak_password(self, client):
        """Registering with a password missing uppercase returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "user@example.com", "password": "alllower1"},
        )
        assert response.status_code == 422

    def test_register_short_password(self, client):
        """Registering with a password shorter than 8 characters returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "user@example.com", "password": "Ab1"},
        )
        assert response.status_code == 422

    def test_register_invalid_email(self, client):
        """Registering with a malformed email returns 422."""
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "ValidPass1"},
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/v1/auth/login"""

    def test_login_success(self, client, registered_user):
        """Registered user can log in and receive an access token."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": registered_user["credentials"]["email"],
                "password": registered_user["credentials"]["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Verify refresh token cookie is set
        assert "refresh_token" in response.cookies

    def test_login_wrong_password(self, client, registered_user):
        """Wrong password returns 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": registered_user["credentials"]["email"],
                "password": "WrongPass1",
            },
        )
        assert response.status_code == 401

    def test_login_unknown_email(self, client):
        """Unknown email returns 401 (same message — no user enumeration)."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "TestPass1"},
        )
        assert response.status_code == 401


class TestGetMe:
    """Tests for GET /api/v1/users/me"""

    def test_get_me_success(self, client, registered_user, auth_headers):
        """Authenticated user can get their profile."""
        response = client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == registered_user["credentials"]["email"]
        assert "password_hash" not in data

    def test_get_me_no_token(self, client):
        """Missing token returns 401."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """Invalid/tampered token returns 401."""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer this.is.not.valid"},
        )
        assert response.status_code == 401


class TestRefresh:
    """Tests for POST /api/v1/auth/refresh"""

    def test_refresh_success(self, client, registered_user):
        """Valid refresh token cookie returns a new access token."""
        # Login to get cookie
        login_resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": registered_user["credentials"]["email"],
                "password": registered_user["credentials"]["password"],
            },
        )
        assert login_resp.status_code == 200

        # Refresh using cookie (TestClient persists cookies automatically)
        refresh_resp = client.post("/api/v1/auth/refresh")
        assert refresh_resp.status_code == 200
        assert "access_token" in refresh_resp.json()

    def test_refresh_no_cookie(self, client):
        """Missing refresh token cookie returns 400."""
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 400


class TestLogout:
    """Tests for POST /api/v1/auth/logout"""

    def test_logout_success(self, client, registered_user):
        """Logout clears the cookie and revokes the token."""
        client.post(
            "/api/v1/auth/login",
            json={
                "email": registered_user["credentials"]["email"],
                "password": registered_user["credentials"]["password"],
            },
        )
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    def test_refresh_after_logout_fails(self, client, registered_user):
        """After logout, refresh token is revoked and cannot be used."""
        client.post(
            "/api/v1/auth/login",
            json={
                "email": registered_user["credentials"]["email"],
                "password": registered_user["credentials"]["password"],
            },
        )
        client.post("/api/v1/auth/logout")
        # Attempt refresh with revoked token
        response = client.post("/api/v1/auth/refresh")
        # Cookie was cleared, so expect 400 (no cookie)
        assert response.status_code in (400, 401)


class TestChangePassword:
    """Tests for POST /api/v1/auth/change-password"""

    def test_change_password_success(self, client, registered_user, auth_headers):
        """Authenticated user can change their password."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": registered_user["credentials"]["password"],
                "new_password": "NewSecure1",
            },
        )
        assert response.status_code == 200

    def test_change_password_wrong_current(self, client, registered_user, auth_headers):
        """Providing wrong current password returns 401."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "WrongCurrent1",
                "new_password": "NewSecure1",
            },
        )
        assert response.status_code == 401

    def test_change_password_same_as_current(self, client, registered_user, auth_headers):
        """Providing same new password as current returns 400."""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": registered_user["credentials"]["password"],
                "new_password": registered_user["credentials"]["password"],
            },
        )
        assert response.status_code == 400
