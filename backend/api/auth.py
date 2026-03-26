from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional

from core.database import get_db
from core.auth import (
    verify_password, get_password_hash, create_access_token, get_current_user
)
from models.user import User, OAuthToken, OTP
from services.gmail_service import get_auth_url, exchange_code_for_tokens
from core.config import get_settings
import secrets
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory state store for OAuth CSRF (use Redis in production)
_oauth_states: dict = {}


class LoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginRequest(BaseModel):
    """Special admin login endpoint"""
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    otp: str

class SendOTPRequest(BaseModel):
    email: EmailStr
    purpose: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
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


@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Verify OTP
    otp_res = await db.execute(
        select(OTP).where(
            OTP.email == data.email, 
            OTP.purpose == "register",
            OTP.code == data.otp
        ).order_by(OTP.id.desc())
    )
    otp_entry = otp_res.scalars().first()
    if not otp_entry:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
    
    try:
        if otp_entry.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Expired OTP code")
    except Exception:
        # Fallback if tzinfo fails
        pass

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        is_admin=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_admin=user.is_admin,
    )

@router.post("/send-otp")
async def send_otp(data: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    if data.purpose not in ["register", "reset"]:
        raise HTTPException(status_code=400, detail="Invalid purpose")
    
    if data.purpose == "reset":
        result = await db.execute(select(User).where(User.email == data.email))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Email not found")
            
    code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    db.add(OTP(email=data.email, code=code, purpose=data.purpose, expires_at=expires_at))
    await db.commit()
    
    sys_email = os.getenv("SYSTEM_EMAIL")
    sys_pass = os.getenv("SYSTEM_EMAIL_PASSWORD")
    if not sys_email or not sys_pass:
        print(f"--- OTP FOR {data.email} ({data.purpose}): {code} ---")
        return {"message": "OTP printed to console (SMTP not setup)"}
        
    try:
        msg = EmailMessage()
        msg["Subject"] = "Your Claim360 OTP Code"
        msg["From"] = f"Claim360 <{sys_email}>"
        msg["To"] = data.email
        msg.set_content(f"Your OTP code for {data.purpose} is: {code}\nThis code will expire in 10 minutes.")
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sys_email, sys_pass)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMTP Error: {str(e)}")
        
    return {"message": "OTP sent to your email"}

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    otp_res = await db.execute(select(OTP).where(OTP.email == data.email, OTP.purpose == "reset", OTP.code == data.otp).order_by(OTP.id.desc()))
    otp_entry = otp_res.scalars().first()
    if not otp_entry: raise HTTPException(status_code=400, detail="Invalid OTP code")
    
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = get_password_hash(data.new_password)
    # disconnect gmail forcing re-auth
    tok_result = await db.execute(select(OAuthToken).where(OAuthToken.user_id == user.id))
    ex_token = tok_result.scalar_one_or_none()
    if ex_token: ex_token.is_valid = False
    
    await db.commit()
    return {"message": "Password updated successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    # ── Force Gmail re-connect on every login (security) ──────────────────
    tok_result = await db.execute(select(OAuthToken).where(OAuthToken.user_id == user.id))
    existing_token = tok_result.scalar_one_or_none()
    if existing_token:
        existing_token.is_valid = False
        await db.commit()

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_admin=user.is_admin,
    )


@router.post("/admin/login", response_model=TokenResponse)
async def admin_login(data: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    """
    🛡️ Admin-only login endpoint
    
    Must provide email and password of a user marked as admin.
    Same as /login but explicitly for admin accounts.
    """
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # ── Check if user is admin ─────────────────────────────────────────────
    if not user.is_admin:
        logger.warning(f"Unauthorized admin login attempt from non-admin user: {data.email}")
        raise HTTPException(status_code=403, detail="Only admin users can access this endpoint")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    # ── Force Gmail re-connect on every login (security) ──────────────────
    tok_result = await db.execute(select(OAuthToken).where(OAuthToken.user_id == user.id))
    existing_token = tok_result.scalar_one_or_none()
    if existing_token:
        existing_token.is_valid = False
        await db.commit()

    token = create_access_token({"sub": str(user.id)})
    logger.info(f"Admin login successful: {data.email}")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_admin=user.is_admin,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == current_user.id, OAuthToken.is_valid == True)
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
async def get_oauth_url(current_user: User = Depends(get_current_user)):
    state = secrets.token_urlsafe(16)
    _oauth_states[state] = current_user.id
    url = get_auth_url(state)
    return {"url": url, "state": state}


@router.get("/oauth/callback")
async def oauth_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    user_id = _oauth_states.pop(state, None)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    token = await exchange_code_for_tokens(code, db, user_id)
    # Redirect to desktop app with success signal
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(url=f"{frontend_url}/oauth/callback?success=1")


@router.delete("/oauth/disconnect")
async def disconnect_oauth(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == current_user.id)
    )
    token = result.scalar_one_or_none()
    if token:
        token.is_valid = False
        await db.commit()
    return {"message": "Gmail disconnected successfully"}
