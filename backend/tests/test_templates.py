"""
Tests for /api/templates/ — CRUD and shared templates.
"""
import pytest
from tests.conftest import auth_header


# ═══════════════════════════════════════════════════════════════════════════
# GET /api/templates/
# ═══════════════════════════════════════════════════════════════════════════

class TestListTemplates:
    async def test_list_own_templates(self, client, regular_user):
        _, token = regular_user
        # Create one
        await client.post("/api/templates/", json={
            "name": "Mine", "subject": "Subj", "body_html": "<p>hi</p>",
        }, headers=auth_header(token))

        resp = await client.get("/api/templates/", headers=auth_header(token))
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
        assert resp.json()[0]["name"] == "Mine"

    async def test_list_includes_shared_templates(
        self, client, db_session, admin_user, regular_user
    ):
        """Regular user should see templates shared by admin."""
        _, admin_token = admin_user
        _, user_token = regular_user

        # Admin creates a shared template
        await client.post("/api/templates/", json={
            "name": "SharedTpl", "subject": "S", "body_html": "<p>shared</p>",
            "is_shared": True,
        }, headers=auth_header(admin_token))

        # Regular user lists templates — should include the shared one
        resp = await client.get("/api/templates/", headers=auth_header(user_token))
        assert resp.status_code == 200
        names = [t["name"] for t in resp.json()]
        assert "SharedTpl" in names

    async def test_list_empty(self, client, regular_user):
        _, token = regular_user
        resp = await client.get("/api/templates/", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json() == []


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/templates/
# ═══════════════════════════════════════════════════════════════════════════

class TestCreateTemplate:
    async def test_create_valid_template(self, client, regular_user):
        _, token = regular_user
        resp = await client.post("/api/templates/", json={
            "name": "Welcome",
            "subject": "Welcome {{name}}",
            "body_html": "<h1>Hello {{name}}</h1>",
            "variables": ["name"],
        }, headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Welcome"
        assert data["variables"] == ["name"]

    async def test_create_template_missing_body(self, client, regular_user):
        _, token = regular_user
        resp = await client.post("/api/templates/", json={
            "name": "NoBody",
            "subject": "Sub",
        }, headers=auth_header(token))
        assert resp.status_code == 422  # body_html is required

    async def test_create_template_missing_name(self, client, regular_user):
        _, token = regular_user
        resp = await client.post("/api/templates/", json={
            "subject": "Sub",
            "body_html": "<p>ok</p>",
        }, headers=auth_header(token))
        assert resp.status_code == 422

    async def test_non_admin_cannot_share(self, client, regular_user):
        """Regular user setting is_shared=True should be silently ignored."""
        _, token = regular_user
        resp = await client.post("/api/templates/", json={
            "name": "TryShare",
            "subject": "S",
            "body_html": "<p>x</p>",
            "is_shared": True,
        }, headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["is_shared"] is False

    async def test_no_auth(self, client):
        resp = await client.post("/api/templates/", json={
            "name": "X", "subject": "S", "body_html": "<p></p>",
        })
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════
# DELETE /api/templates/{id}
# ═══════════════════════════════════════════════════════════════════════════

class TestDeleteTemplate:
    async def test_delete_own_template(self, client, regular_user):
        _, token = regular_user
        create = await client.post("/api/templates/", json={
            "name": "Del", "subject": "S", "body_html": "<p></p>",
        }, headers=auth_header(token))
        tid = create.json()["id"]

        resp = await client.delete(f"/api/templates/{tid}", headers=auth_header(token))
        assert resp.status_code == 200

    async def test_delete_other_users_template(self, client, regular_user, second_user):
        _, token1 = regular_user
        _, token2 = second_user

        create = await client.post("/api/templates/", json={
            "name": "User1Tpl", "subject": "S", "body_html": "<p></p>",
        }, headers=auth_header(token1))
        tid = create.json()["id"]

        resp = await client.delete(f"/api/templates/{tid}", headers=auth_header(token2))
        assert resp.status_code == 403

    async def test_delete_nonexistent(self, client, regular_user):
        _, token = regular_user
        resp = await client.delete("/api/templates/99999", headers=auth_header(token))
        assert resp.status_code == 404

    async def test_admin_can_delete_any(self, client, regular_user, admin_user):
        """Admin should be able to delete any user's template."""
        _, user_token = regular_user
        _, admin_token = admin_user

        create = await client.post("/api/templates/", json={
            "name": "UserTpl", "subject": "S", "body_html": "<p></p>",
        }, headers=auth_header(user_token))
        tid = create.json()["id"]

        resp = await client.delete(f"/api/templates/{tid}", headers=auth_header(admin_token))
        assert resp.status_code == 200
