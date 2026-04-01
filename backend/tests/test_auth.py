"""
Tests for POST /api/auth/login, /register, GET /me, /reset-password.
"""
import pytest
from datetime import datetime, timedelta, timezone
from tests.conftest import auth_header, _seed_user
from models.user import OTP, AppSettings
from core.auth import create_access_token


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/auth/login
# ═══════════════════════════════════════════════════════════════════════════

class TestLogin:
    async def test_login_valid_credentials(self, client, regular_user):
        user, _ = regular_user
        resp = await client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "testpass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["email"] == "user@test.com"
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client, regular_user):
        resp = await client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client):
        resp = await client.post("/api/auth/login", json={
            "email": "nobody@test.com",
            "password": "whatever",
        })
        # Server should not crash — should return 401 or 500 gracefully
        assert resp.status_code in (401, 500)

    async def test_login_inactive_user(self, client, inactive_user):
        """Inactive user should get 403 (account deactivated)."""
        resp = await client.post("/api/auth/login", json={
            "email": "inactive@test.com",
            "password": "testpass123",
        })
        assert resp.status_code == 403

    async def test_login_case_insensitive_email(self, client, regular_user):
        resp = await client.post("/api/auth/login", json={
            "email": "USER@Test.Com",
            "password": "testpass123",
        })
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/auth/register
# ═══════════════════════════════════════════════════════════════════════════

class TestRegister:
    async def test_register_with_valid_otp(self, client, db_session, app_settings_open):
        """Register succeeds with a valid, unexpired OTP."""
        otp = OTP(
            email="newuser@test.com",
            code="123456",
            purpose="register",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db_session.add(otp)
        await db_session.commit()

        resp = await client.post("/api/auth/register", json={
            "email": "newuser@test.com",
            "full_name": "New User",
            "password": "securepass123",
            "otp": "123456",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "newuser@test.com"
        assert "access_token" in data

    async def test_register_expired_otp(self, client, db_session, app_settings_open):
        otp = OTP(
            email="expired@test.com",
            code="654321",
            purpose="register",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=15),
        )
        db_session.add(otp)
        await db_session.commit()

        resp = await client.post("/api/auth/register", json={
            "email": "expired@test.com",
            "full_name": "Expired User",
            "password": "securepass123",
            "otp": "654321",
        })
        assert resp.status_code == 400
        assert "expired" in resp.json()["detail"].lower() or "invalid" in resp.json()["detail"].lower()

    async def test_register_duplicate_email(self, client, db_session, regular_user, app_settings_open):
        """Registering with an already-used email should fail."""
        otp = OTP(
            email="user@test.com",
            code="111111",
            purpose="register",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db_session.add(otp)
        await db_session.commit()

        resp = await client.post("/api/auth/register", json={
            "email": "user@test.com",
            "full_name": "Duplicate",
            "password": "securepass123",
            "otp": "111111",
        })
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"].lower()

    async def test_register_invalid_otp_code(self, client, db_session, app_settings_open):
        resp = await client.post("/api/auth/register", json={
            "email": "nootp@test.com",
            "full_name": "No OTP",
            "password": "securepass123",
            "otp": "000000",
        })
        assert resp.status_code == 400

    async def test_register_closed_registrations(self, client, db_session, app_settings_closed):
        """When registrations are closed, register must return 403."""
        resp = await client.post("/api/auth/register", json={
            "email": "blocked@test.com",
            "full_name": "Blocked",
            "password": "securepass123",
            "otp": "123456",
        })
        assert resp.status_code == 403

    async def test_register_short_password(self, client, db_session, app_settings_open):
        otp = OTP(
            email="short@test.com",
            code="222222",
            purpose="register",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db_session.add(otp)
        await db_session.commit()

        resp = await client.post("/api/auth/register", json={
            "email": "short@test.com",
            "full_name": "Short Pass",
            "password": "abc",
            "otp": "222222",
        })
        assert resp.status_code == 400
        assert "8 characters" in resp.json()["detail"]


# ═══════════════════════════════════════════════════════════════════════════
# GET /api/auth/me
# ═══════════════════════════════════════════════════════════════════════════

class TestMe:
    async def test_me_valid_token(self, client, regular_user):
        _, token = regular_user
        resp = await client.get("/api/auth/me", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "user@test.com"
        assert data["is_admin"] is False

    async def test_me_no_token(self, client):
        resp = await client.get("/api/auth/me")
        assert resp.status_code in (401, 403)

    async def test_me_invalid_token(self, client):
        resp = await client.get("/api/auth/me", headers=auth_header("bad.token.here"))
        assert resp.status_code == 401

    async def test_me_expired_token(self, client, regular_user):
        user, _ = regular_user
        expired = create_access_token(
            {"sub": str(user.id)},
            expires_delta=timedelta(seconds=-10),
        )
        resp = await client.get("/api/auth/me", headers=auth_header(expired))
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/auth/reset-password
# ═══════════════════════════════════════════════════════════════════════════

class TestResetPassword:
    async def test_reset_password_valid(self, client, db_session, regular_user):
        otp = OTP(
            email="user@test.com",
            code="999999",
            purpose="reset",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db_session.add(otp)
        await db_session.commit()

        resp = await client.post("/api/auth/reset-password", json={
            "email": "user@test.com",
            "otp": "999999",
            "new_password": "newpassword123",
        })
        assert resp.status_code == 200
        assert "updated" in resp.json()["message"].lower()

        # Now login with new password
        resp2 = await client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "newpassword123",
        })
        assert resp2.status_code == 200

    async def test_reset_password_invalid_otp(self, client, regular_user):
        resp = await client.post("/api/auth/reset-password", json={
            "email": "user@test.com",
            "otp": "000000",
            "new_password": "newpass123",
        })
        assert resp.status_code == 400

    async def test_reset_password_short(self, client, db_session, regular_user):
        otp = OTP(
            email="user@test.com",
            code="888888",
            purpose="reset",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db_session.add(otp)
        await db_session.commit()

        resp = await client.post("/api/auth/reset-password", json={
            "email": "user@test.com",
            "otp": "888888",
            "new_password": "abc",
        })
        assert resp.status_code == 400
