from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional

from core.database import get_db
from core.auth import (
    verify_password, get_password_hash, create_access_token, get_current_user
)
from models.user import User, OAuthToken, OTP, OAuthState, AppSettings
from services.gmail_service import get_auth_url, exchange_code_for_tokens
from core.config import get_settings
import secrets
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Pydantic models ────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    otp: str


class SendOTPRequest(BaseModel):
    email: EmailStr
    purpose: str  # 'register' | 'reset'


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    id: int
    email: str
    full_name: str
    is_admin: bool


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_admin: bool
    is_active: bool
    gmail_connected: bool
    gmail_email: Optional[str]

    class Config:
        from_attributes = True


# ── Helpers ────────────────────────────────────────────────────────────────────

def send_otp_email_task(email: str, purpose: str, code: str, sys_email: str, sys_pass: str):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Your Claim360 OTP Code"
        msg["From"] = f"Claim360 <{sys_email}>"
        msg["To"] = email
        msg.set_content(
            f"Your OTP code for {purpose} is: {code}\nThis code will expire in 10 minutes."
        )
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sys_email, sys_pass)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        logger.error(f"SMTP Error for {email}: {str(e)}")


async def _get_or_create_settings(db: AsyncSession) -> AppSettings:
    """Return the single AppSettings row, creating it if absent."""
    result = await db.execute(select(AppSettings))
    row = result.scalars().first()
    if not row:
        row = AppSettings(registrations_open=False)
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row


# ── Public auth endpoints ──────────────────────────────────────────────────────

@router.get("/registrations-status")
async def registrations_status(db: AsyncSession = Depends(get_db)):
    """Public endpoint — lets the login page know if sign-up is allowed."""
    try:
        app_cfg = await _get_or_create_settings(db)
        return {"open": app_cfg.registrations_open}
    except Exception as e:
        logger.error(f"Error fetching registrations-status: {str(e)}")
        # If DB not ready yet, default to closed for safety
        return {"open": False}


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Unified login for both admins and regular users.
    The backend auto-detects role — no separate admin endpoint needed.
    """
    try:
        email_lower = data.email.lower().strip()
        result = await db.execute(select(User).where(User.email == email_lower))
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account deactivated. Contact your admin.")

        # Force Gmail re-connect on every login (security)
        tok_result = await db.execute(select(OAuthToken).where(OAuthToken.user_id == user.id))
        existing_token = tok_result.scalar_one_or_none()
        if existing_token:
            existing_token.is_valid = False
            await db.commit()

        if user.is_admin:
            logger.info(f"Admin login: {email_lower}")
        else:
            logger.info(f"User login: {email_lower}")

        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_admin=user.is_admin,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LOGIN CRASH: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Database error or server crash: {str(e)}")


@router.post("/send-otp")
async def send_otp(
    data: SendOTPRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    email_lower = data.email.lower().strip()
    if data.purpose not in ["register", "reset"]:
        raise HTTPException(status_code=400, detail="Invalid purpose")

    if data.purpose == "reset":
        result = await db.execute(select(User).where(User.email == email_lower))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="No account found with that email")

    if data.purpose == "register":
        # Only allow OTP for registration if registrations are open
        app_cfg = await _get_or_create_settings(db)
        if not app_cfg.registrations_open:
            raise HTTPException(
                status_code=403,
                detail="Registrations are currently closed. Contact your admin."
            )

    code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    db.add(OTP(email=email_lower, code=code, purpose=data.purpose, expires_at=expires_at))
    await db.commit()

    sys_email = os.getenv("SYSTEM_EMAIL")
    sys_pass = os.getenv("SYSTEM_EMAIL_PASSWORD")

    if not sys_email or not sys_pass:
        logger.warning(f"--- OTP FOR {email_lower} ({data.purpose}): {code} (SMTP not configured) ---")
        return {"message": f"OTP printed to server console (SMTP not configured). Code: {code}"}

    background_tasks.add_task(send_otp_email_task, email_lower, data.purpose, code, sys_email, sys_pass)
    return {"message": "OTP sent to your email"}


@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Guard: registrations must be open
    app_cfg = await _get_or_create_settings(db)
    if not app_cfg.registrations_open:
        raise HTTPException(
            status_code=403,
            detail="Registrations are currently closed. Contact your admin."
        )

    email_lower = data.email.lower().strip()

    # Check duplicate
    result = await db.execute(select(User).where(User.email == email_lower))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="An account with that email already exists")

    # Verify OTP
    otp_res = await db.execute(
        select(OTP).where(
            OTP.email == email_lower,
            OTP.purpose == "register",
            OTP.code == data.otp,
        ).order_by(OTP.id.desc())
    )
    otp_entry = otp_res.scalars().first()
    if not otp_entry:
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    try:
        if otp_entry.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="OTP has expired — please request a new one")
    except AttributeError:
        pass  # naive datetime edge-case; skip expiry check

    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user = User(
        email=email_lower,
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        is_admin=False,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_admin=user.is_admin,
    )


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    email_lower = data.email.lower().strip()

    otp_res = await db.execute(
        select(OTP).where(
            OTP.email == email_lower,
            OTP.purpose == "reset",
            OTP.code == data.otp,
        ).order_by(OTP.id.desc())
    )
    otp_entry = otp_res.scalars().first()
    if not otp_entry:
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    try:
        if otp_entry.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="OTP has expired — please request a new one")
    except AttributeError:
        pass

    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    result = await db.execute(select(User).where(User.email == email_lower))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = get_password_hash(data.new_password)

    # Invalidate existing Gmail token (force re-auth)
    tok_result = await db.execute(select(OAuthToken).where(OAuthToken.user_id == user.id))
    ex_token = tok_result.scalar_one_or_none()
    if ex_token:
        ex_token.is_valid = False

    await db.commit()
    return {"message": "Password updated successfully. Please sign in with your new password."}


# ── Authenticated endpoints ────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OAuthToken).where(
            OAuthToken.user_id == current_user.id,
            OAuthToken.is_valid == True,
        )
    )
    token = result.scalar_one_or_none()
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_admin=current_user.is_admin,
        is_active=current_user.is_active,
        gmail_connected=token is not None,
        gmail_email=token.gmail_email if token else None,
    )


@router.get("/oauth/url")
async def get_oauth_url(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    state = secrets.token_urlsafe(16)
    db.add(OAuthState(state=state, user_id=current_user.id))
    await db.commit()
    url = get_auth_url(state)
    return {"url": url, "state": state}


@router.get("/oauth/callback")
async def oauth_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    st_result = await db.execute(select(OAuthState).where(OAuthState.state == state))
    st_entry = st_result.scalar_one_or_none()

    if not st_entry:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    user_id = st_entry.user_id
    await db.delete(st_entry)
    await db.commit()

    try:
        token = await exchange_code_for_tokens(code, db, user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not settings.FRONTEND_URL:
        raise HTTPException(status_code=500, detail="FRONTEND_URL not configured on server")

    return RedirectResponse(url=f"{settings.FRONTEND_URL.rstrip('/')}/oauth/callback?success=1")


@router.delete("/oauth/disconnect")
async def disconnect_oauth(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(OAuthToken).where(OAuthToken.user_id == current_user.id))
    token = result.scalar_one_or_none()
    if token:
        token.is_valid = False
        await db.commit()
    return {"message": "Gmail disconnected successfully"}
