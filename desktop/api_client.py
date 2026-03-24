"""Centralized API client for Claim360 desktop app."""
import requests
from typing import Optional, Dict, Any, List
import json


class APIError(Exception):
    def __init__(self, message: str, status_code: int = 0):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class Claim360API:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.user_info: Optional[Dict] = None
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def set_token(self, token: str):
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def clear_token(self):
        self.token = None
        self.session.headers.pop("Authorization", None)
        self.user_info = None

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _handle_response(self, response: requests.Response) -> Any:
        if response.status_code == 401:
            raise APIError("Session expired. Please log in again.", 401)
        if response.status_code == 403:
            raise APIError("Access denied.", 403)
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise APIError(str(detail), response.status_code)
        try:
            return response.json()
        except Exception:
            return response.text

    # ── Auth ─────────────────────────────────────────────────────────
    def login(self, email: str, password: str) -> Dict:
        r = self.session.post(self._url("/api/auth/login"), json={"email": email, "password": password})
        data = self._handle_response(r)
        self.set_token(data["access_token"])
        self.user_info = data
        return data

    def register(self, email: str, full_name: str, password: str) -> Dict:
        r = self.session.post(self._url("/api/auth/register"), json={
            "email": email, "full_name": full_name, "password": password
        })
        data = self._handle_response(r)
        self.set_token(data["access_token"])
        self.user_info = data
        return data

    def get_me(self) -> Dict:
        r = self.session.get(self._url("/api/auth/me"))
        return self._handle_response(r)

    def get_oauth_url(self) -> str:
        r = self.session.get(self._url("/api/auth/oauth/url"))
        return self._handle_response(r)["url"]

    def disconnect_oauth(self):
        r = self.session.delete(self._url("/api/auth/oauth/disconnect"))
        return self._handle_response(r)

    # ── Templates ─────────────────────────────────────────────────────
    def list_templates(self) -> List[Dict]:
        r = self.session.get(self._url("/api/templates/"))
        return self._handle_response(r)

    def create_template(self, data: Dict) -> Dict:
        r = self.session.post(self._url("/api/templates/"), json=data)
        return self._handle_response(r)

    def update_template(self, template_id: int, data: Dict) -> Dict:
        r = self.session.put(self._url(f"/api/templates/{template_id}"), json=data)
        return self._handle_response(r)

    def delete_template(self, template_id: int):
        r = self.session.delete(self._url(f"/api/templates/{template_id}"))
        return self._handle_response(r)

    def upload_attachment(self, filepath: str, is_shared: bool = False) -> Dict:
        with open(filepath, "rb") as f:
            import os, mimetypes
            filename = os.path.basename(filepath)
            mime = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
            r = self.session.post(
                self._url("/api/templates/attachments/upload"),
                files={"file": (filename, f, mime)},
                data={"is_shared": str(is_shared).lower()},
                headers={k: v for k, v in self.session.headers.items() if k != "Content-Type"},
            )
        return self._handle_response(r)

    def list_attachments(self) -> List[Dict]:
        r = self.session.get(self._url("/api/templates/attachments/"))
        return self._handle_response(r)

    def delete_attachment(self, att_id: int):
        r = self.session.delete(self._url(f"/api/templates/attachments/{att_id}"))
        return self._handle_response(r)

    # ── Data ──────────────────────────────────────────────────────────
    def parse_excel(self, filepath: str) -> Dict:
        with open(filepath, "rb") as f:
            import os
            filename = os.path.basename(filepath)
            r = self.session.post(
                self._url("/api/data/parse-excel"),
                files={"file": (filename, f)},
                headers={k: v for k, v in self.session.headers.items() if k != "Content-Type"},
            )
        return self._handle_response(r)

    def get_sample_excel(self, variables: str = "name,company,position") -> bytes:
        r = self.session.get(
            self._url("/api/data/sample-excel"),
            params={"variables": variables},
            stream=True,
        )
        if r.status_code >= 400:
            raise APIError("Failed to download sample", r.status_code)
        return r.content

    def generate_dummy(self, variable_names: List[str], count: int = 10) -> Dict:
        r = self.session.post(self._url("/api/data/generate-dummy"), json={
            "variable_names": variable_names, "count": count
        })
        return self._handle_response(r)

    # ── Campaigns ─────────────────────────────────────────────────────
    def list_campaigns(self) -> List[Dict]:
        r = self.session.get(self._url("/api/campaigns/"))
        return self._handle_response(r)

    def create_campaign(self, data: Dict) -> Dict:
        r = self.session.post(self._url("/api/campaigns/"), json=data)
        return self._handle_response(r)

    def start_campaign(self, campaign_id: int) -> Dict:
        r = self.session.post(self._url(f"/api/campaigns/{campaign_id}/send"))
        return self._handle_response(r)

    def get_campaign_logs(self, campaign_id: int) -> List[Dict]:
        r = self.session.get(self._url(f"/api/campaigns/{campaign_id}/logs"))
        return self._handle_response(r)

    def delete_campaign(self, campaign_id: int):
        r = self.session.delete(self._url(f"/api/campaigns/{campaign_id}"))
        return self._handle_response(r)

    # ── Admin ─────────────────────────────────────────────────────────
    def admin_stats(self) -> Dict:
        r = self.session.get(self._url("/api/admin/stats"))
        return self._handle_response(r)

    def admin_list_users(self) -> List[Dict]:
        r = self.session.get(self._url("/api/admin/users"))
        return self._handle_response(r)

    def admin_toggle_admin(self, user_id: int) -> Dict:
        r = self.session.put(self._url(f"/api/admin/users/{user_id}/toggle-admin"))
        return self._handle_response(r)

    def admin_toggle_active(self, user_id: int) -> Dict:
        r = self.session.put(self._url(f"/api/admin/users/{user_id}/toggle-active"))
        return self._handle_response(r)

    def admin_all_campaigns(self) -> List[Dict]:
        r = self.session.get(self._url("/api/admin/campaigns"))
        return self._handle_response(r)

    def check_health(self) -> bool:
        try:
            r = requests.get(self._url("/health"), timeout=3)
            return r.status_code == 200
        except Exception:
            return False
