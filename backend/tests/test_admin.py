"""
Tests for /api/admin/* — stats, users list, toggle-admin.
"""
import pytest
from tests.conftest import auth_header


# ═══════════════════════════════════════════════════════════════════════════
# GET /api/admin/stats
# ═══════════════════════════════════════════════════════════════════════════

class TestAdminStats:
    async def test_admin_stats_success(self, client, admin_user):
        _, token = admin_user
        resp = await client.get("/api/admin/stats", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "total_users" in data
        assert "total_campaigns" in data
        assert "total_sent" in data

    async def test_admin_stats_regular_user_forbidden(self, client, regular_user):
        _, token = regular_user
        resp = await client.get("/api/admin/stats", headers=auth_header(token))
        assert resp.status_code == 403

    async def test_admin_stats_no_auth(self, client):
        resp = await client.get("/api/admin/stats")
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════
# GET /api/admin/users
# ═══════════════════════════════════════════════════════════════════════════

class TestAdminUsers:
    async def test_list_users_as_admin(self, client, admin_user, regular_user):
        _, token = admin_user
        resp = await client.get("/api/admin/users", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        # At minimum, both admin and regular user should appear
        assert len(data) >= 2
        emails = [u["email"] for u in data]
        assert "admin@test.com" in emails
        assert "user@test.com" in emails

    async def test_list_users_regular_user_forbidden(self, client, regular_user):
        _, token = regular_user
        resp = await client.get("/api/admin/users", headers=auth_header(token))
        assert resp.status_code == 403

    async def test_users_have_expected_fields(self, client, admin_user):
        _, token = admin_user
        resp = await client.get("/api/admin/users", headers=auth_header(token))
        assert resp.status_code == 200
        if resp.json():
            u = resp.json()[0]
            for field in ("id", "email", "full_name", "is_admin", "is_active"):
                assert field in u


# ═══════════════════════════════════════════════════════════════════════════
# PUT /api/admin/users/{id}/toggle-admin
# ═══════════════════════════════════════════════════════════════════════════

class TestToggleAdmin:
    async def test_toggle_admin_promote(self, client, admin_user, regular_user):
        admin, admin_token = admin_user
        user, _ = regular_user

        resp = await client.put(
            f"/api/admin/users/{user.id}/toggle-admin",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["is_admin"] is True

    async def test_toggle_admin_demote(self, client, admin_user, regular_user):
        admin, admin_token = admin_user
        user, _ = regular_user

        # First promote
        await client.put(
            f"/api/admin/users/{user.id}/toggle-admin",
            headers=auth_header(admin_token),
        )
        # Then demote
        resp = await client.put(
            f"/api/admin/users/{user.id}/toggle-admin",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["is_admin"] is False

    async def test_toggle_admin_self_demotion_allowed(self, client, admin_user):
        """
        BUG REPORT: The current code allows an admin to demote themselves.
        This test documents the current behaviour — the endpoint does NOT
        prevent self-demotion. This is flagged as a production issue.
        """
        admin, token = admin_user
        resp = await client.put(
            f"/api/admin/users/{admin.id}/toggle-admin",
            headers=auth_header(token),
        )
        # Currently succeeds (200) — this is the bug being documented
        assert resp.status_code == 200

    async def test_toggle_admin_regular_user_forbidden(self, client, regular_user):
        user, token = regular_user
        resp = await client.put(
            f"/api/admin/users/{user.id}/toggle-admin",
            headers=auth_header(token),
        )
        assert resp.status_code == 403

    async def test_toggle_nonexistent_user(self, client, admin_user):
        _, token = admin_user
        resp = await client.put(
            "/api/admin/users/99999/toggle-admin",
            headers=auth_header(token),
        )
        assert resp.status_code == 404
