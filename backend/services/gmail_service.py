import base64
import os
import hashlib
import secrets
import mimetypes
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from urllib.parse import urlencode

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import requests as http_requests

from core.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import OAuthToken

settings = get_settings()

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_USERINFO  = "https://www.googleapis.com/oauth2/v2/userinfo"

# In-memory PKCE verifier store keyed by state
# (use Redis in production for multi-process deployments)
_pkce_store: dict = {}


def _generate_pkce_pair():
    """Generate a code_verifier and code_challenge for PKCE."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
    return verifier, challenge


def get_auth_url(state: str) -> str:
    """
    Build the Google OAuth authorization URL manually — no PKCE.
    Using plain (non-PKCE) flow so the token exchange works without a verifier.
    """
    params = {
        "client_id":     settings.GOOGLE_CLIENT_ID,
        "redirect_uri":  settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         " ".join(settings.GOOGLE_SCOPES),
        "access_type":   "offline",
        "prompt":        "consent",
        "state":         state,
        "include_granted_scopes": "true",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str, db: AsyncSession, user_id: int) -> OAuthToken:
    """Exchange authorization code for tokens via direct POST (no PKCE)."""
    resp = http_requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code":          code,
            "client_id":     settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri":  settings.GOOGLE_REDIRECT_URI,
            "grant_type":    "authorization_code",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    resp_json = resp.json()

    if not resp.ok:
        err = resp_json.get("error_description") or resp_json.get("error") or resp.text
        import logging
        logging.getLogger("gmail").error(f"Google token exchange failed: {err}")
        raise ValueError(f"Google token exchange failed: {err}")

    access_token  = resp_json["access_token"]
    refresh_token = resp_json.get("refresh_token")
    expires_in    = resp_json.get("expires_in", 3600)
    expiry        = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    # Get user's Gmail address
    userinfo = http_requests.get(
        GOOGLE_USERINFO,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    gmail_email = userinfo.json().get("email") if userinfo.ok else None

    # Upsert token record
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user_id)
    )
    token = result.scalar_one_or_none()

    if token:
        token.access_token  = access_token
        token.token_expiry  = expiry
        token.scopes        = list(settings.GOOGLE_SCOPES)
        token.is_valid      = True
        if refresh_token:
            token.refresh_token = refresh_token
        if gmail_email:
            token.gmail_email = gmail_email
    else:
        token = OAuthToken(
            user_id=user_id,
            gmail_email=gmail_email,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=expiry,
            scopes=list(settings.GOOGLE_SCOPES),
            is_valid=True,
        )
        db.add(token)

    await db.commit()
    await db.refresh(token)
    return token


async def get_credentials(user_id: int, db: AsyncSession) -> Optional[Credentials]:
    result = await db.execute(
        select(OAuthToken).where(
            OAuthToken.user_id == user_id,
            OAuthToken.is_valid == True
        )
    )
    token = result.scalar_one_or_none()
    if not token:
        return None

    creds = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri=GOOGLE_TOKEN_URL,
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=token.scopes or list(settings.GOOGLE_SCOPES),
    )

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token.access_token = creds.token
            token.token_expiry = creds.expiry
            await db.commit()
        except Exception:
            token.is_valid = False
            await db.commit()
            return None

    return creds


def build_email_message(
    sender: str,
    to: List[str],
    cc: List[str],
    subject: str,
    body_html: str,
    body_text: str = "",
    attachments: List[Dict[str, Any]] = None,
    tracking_pixel_url: str = None,
) -> str:
    msg = MIMEMultipart("mixed")
    msg["From"] = sender
    msg["To"]   = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject

    body_part = MIMEMultipart("alternative")
    if body_text:
        body_part.attach(MIMEText(body_text, "plain"))

    html_body = body_html
    if tracking_pixel_url:
        html_body += f'<img src="{tracking_pixel_url}" width="1" height="1" style="display:none;" />'

    body_part.attach(MIMEText(html_body, "html"))
    msg.attach(body_part)

    for att in (attachments or []):
        filepath = att.get("file_path", "")
        if not os.path.exists(filepath):
            continue
        filename  = att.get("original_filename", os.path.basename(filepath))
        mime_type = att.get("mime_type", "application/octet-stream")
        maintype, subtype = mime_type.split("/", 1)
        with open(filepath, "rb") as f:
            part = MIMEBase(maintype, subtype)
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(part)

    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


async def send_email_via_gmail(
    creds: Credentials,
    sender: str,
    to: List[str],
    cc: List[str],
    subject: str,
    body_html: str,
    body_text: str = "",
    attachments: List[Dict] = None,
    tracking_pixel_url: str = None,
) -> str:
    service = build("gmail", "v1", credentials=creds)
    raw = build_email_message(
        sender=sender, to=to, cc=cc,
        subject=subject, body_html=body_html, body_text=body_text,
        attachments=attachments, tracking_pixel_url=tracking_pixel_url,
    )
    result = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()
    return result.get("id")
