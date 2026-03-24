from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr
from typing import Optional
import base64

from core.database import get_db
from services.email_service import record_open
from core.auth import get_current_admin, get_password_hash
from models.user import User, Campaign, EmailLog, EmailStatus

tracking_router = APIRouter(prefix="/api/track", tags=["tracking"])
admin_router    = APIRouter(prefix="/api/admin",  tags=["admin"])

PIXEL_GIF = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")


@tracking_router.get("/{tracking_id}/pixel.gif")
async def tracking_pixel(tracking_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    await record_open(tracking_id, db, ip=ip, ua=ua)
    return Response(content=PIXEL_GIF, media_type="image/gif",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"})


# ── Pydantic schemas ────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    is_admin: bool = False

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


# ── Admin: stats ─────────────────────────────────────────────────────────
@admin_router.get("/stats")
async def admin_stats(admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    total_users     = (await db.execute(select(func.count(User.id)))).scalar()
    total_campaigns = (await db.execute(select(func.count(Campaign.id)))).scalar()
    total_sent      = (await db.execute(select(func.count(EmailLog.id)).where(EmailLog.status == EmailStatus.sent))).scalar()
    total_opened    = (await db.execute(select(func.count(EmailLog.id)).where(EmailLog.status == EmailStatus.opened))).scalar()
    total_failed    = (await db.execute(select(func.count(EmailLog.id)).where(EmailLog.status == EmailStatus.failed))).scalar()
    return {"total_users": total_users, "total_campaigns": total_campaigns,
            "total_sent": total_sent, "total_opened": total_opened, "total_failed": total_failed}


# ── Admin: list users ─────────────────────────────────────────────────────
@admin_router.get("/users")
async def admin_list_users(admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    out = []
    for u in users:
        ccount = (await db.execute(select(func.count(Campaign.id)).where(Campaign.user_id == u.id))).scalar()
        scount = (await db.execute(select(func.count(EmailLog.id)).where(
            EmailLog.user_id == u.id, EmailLog.status.in_([EmailStatus.sent, EmailStatus.opened])))).scalar()
        out.append({"id": u.id, "email": u.email, "full_name": u.full_name,
                    "is_admin": u.is_admin, "is_active": u.is_active,
                    "campaigns": ccount, "emails_sent": scount, "created_at": str(u.created_at)})
    return out


# ── Admin: create user ────────────────────────────────────────────────────
@admin_router.post("/users")
async def admin_create_user(data: UserCreate, admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=data.email, full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        is_admin=data.is_admin, is_active=True,
    )
    db.add(user); await db.commit(); await db.refresh(user)
    return {"id": user.id, "email": user.email, "full_name": user.full_name,
            "is_admin": user.is_admin, "is_active": user.is_active}


# ── Admin: update user ────────────────────────────────────────────────────
@admin_router.put("/users/{user_id}")
async def admin_update_user(user_id: int, data: UserUpdate,
    admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if data.full_name is not None: user.full_name = data.full_name
    if data.email     is not None: user.email     = data.email
    if data.is_admin  is not None: user.is_admin  = data.is_admin
    if data.is_active is not None: user.is_active = data.is_active
    if data.password:
        user.hashed_password = get_password_hash(data.password)
    await db.commit(); await db.refresh(user)
    return {"id": user.id, "email": user.email, "full_name": user.full_name,
            "is_admin": user.is_admin, "is_active": user.is_active}


# ── Admin: delete user ────────────────────────────────────────────────────
@admin_router.delete("/users/{user_id}")
async def admin_delete_user(user_id: int, admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    await db.delete(user); await db.commit()
    return {"message": f"User {user.email} deleted"}


# ── Admin: toggle admin/active (kept for backward compat) ─────────────────
@admin_router.put("/users/{user_id}/toggle-admin")
async def toggle_admin(user_id: int, admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = not user.is_admin; await db.commit()
    return {"id": user.id, "is_admin": user.is_admin}

@admin_router.put("/users/{user_id}/toggle-active")
async def toggle_active(user_id: int, admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active; await db.commit()
    return {"id": user.id, "is_active": user.is_active}


# ── Admin: all campaigns ──────────────────────────────────────────────────
@admin_router.get("/campaigns")
async def admin_all_campaigns(admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Campaign, User.email, User.full_name)
        .join(User, Campaign.user_id == User.id)
        .order_by(Campaign.created_at.desc())
    )
    return [{"id": c.id, "name": c.name, "status": c.status, "total_emails": c.total_emails,
             "sent_count": c.sent_count, "failed_count": c.failed_count, "opened_count": c.opened_count,
             "user_email": email, "user_name": name, "created_at": str(c.created_at)}
            for c, email, name in result.all()]
