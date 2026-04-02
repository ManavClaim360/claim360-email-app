from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Dict

from core.database import get_db
from core.auth import get_current_user, get_current_admin
from models.user import User, Signature

router = APIRouter(prefix="/api/signatures", tags=["signatures"])


class SignaturePayload(BaseModel):
    name:            Optional[str] = "My Signature"
    is_default:      Optional[bool] = True
    is_shared:       Optional[bool] = False
    full_name:       Optional[str] = None
    title:           Optional[str] = None
    company:         Optional[str] = "CLAIM 360"
    phone:           Optional[str] = None
    website:         Optional[str] = None
    email_addr:      Optional[str] = None
    address_mumbai:  Optional[str] = None
    address_delhi:   Optional[str] = None
    address_london:  Optional[str] = None
    cin:             Optional[str] = None
    copyright_text:  Optional[str] = None
    logo_url:        Optional[str] = None
    brand_color:     Optional[str] = "#1C305E"
    social_links:    Optional[Dict[str, str]] = None   # {whatsapp, linkedin, location, twitter, instagram}


def sig_to_dict(s: Signature) -> dict:
    return {
        "id": s.id, "user_id": s.user_id,
        "name": s.name, "is_default": s.is_default, "is_shared": s.is_shared,
        "full_name": s.full_name, "title": s.title, "company": s.company,
        "phone": s.phone, "website": s.website, "email_addr": s.email_addr,
        "address_mumbai": s.address_mumbai, "address_delhi": s.address_delhi,
        "address_london": s.address_london, "cin": s.cin,
        "copyright_text": s.copyright_text, "logo_url": s.logo_url,
        "brand_color": s.brand_color,
        "social_links": s.social_links or {},
        "created_at": str(s.created_at),
    }


@router.get("/me")
async def get_my_signature(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Always returns 200. exists=False when no signature saved yet."""
    try:
        result = await db.execute(
            select(Signature).where(Signature.user_id == current_user.id)
        )
        sig = result.scalar_one_or_none()
        if not sig:
            return {"exists": False, "is_default": False}
        return {**sig_to_dict(sig), "exists": True}
    except Exception as e:
        # Table may not exist yet — return empty instead of 500/404
        return {"exists": False, "is_default": False, "error": str(e)}


@router.post("/me")
async def save_my_signature(
    data: SignaturePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Signature).where(Signature.user_id == current_user.id)
    )
    sig = result.scalar_one_or_none()

    fields = data.model_dump()
    if sig:
        for k, v in fields.items():
            setattr(sig, k, v)
    else:
        sig = Signature(user_id=current_user.id, **fields)
        db.add(sig)

    await db.commit()
    await db.refresh(sig)
    return {**sig_to_dict(sig), "exists": True}


@router.delete("/me")
async def delete_my_signature(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Signature).where(Signature.user_id == current_user.id)
    )
    sig = result.scalar_one_or_none()
    if sig:
        await db.delete(sig)
        await db.commit()
    return {"message": "deleted"}


# ── Admin Routes ────────────────────────────────────────────────────────
@router.get("/admin/all")
async def get_all_signatures(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Signature, User.email, User.full_name)
        .join(User, Signature.user_id == User.id)
    )
    return [{**sig_to_dict(s), "user_email": e, "user_name": n} for s, e, n in result.all()]

@router.get("/admin/{user_id}")
async def admin_get_signature(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(Signature).where(Signature.user_id == user_id))
        sig = result.scalar_one_or_none()
        if not sig: return {"exists": False, "is_default": False}
        return {**sig_to_dict(sig), "exists": True}
    except Exception as e:
        return {"exists": False, "is_default": False, "error": str(e)}

@router.put("/admin/{user_id}")
async def admin_save_signature(
    user_id: int,
    data: SignaturePayload,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Signature).where(Signature.user_id == user_id))
    sig = result.scalar_one_or_none()
    fields = data.model_dump()
    if sig:
        for k, v in fields.items(): setattr(sig, k, v)
    else:
        sig = Signature(user_id=user_id, **fields)
        db.add(sig)
    await db.commit(); await db.refresh(sig)
    return {**sig_to_dict(sig), "exists": True}

@router.delete("/admin/{user_id}")
async def admin_delete_signature(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Signature).where(Signature.user_id == user_id))
    sig = result.scalar_one_or_none()
    if sig:
        await db.delete(sig)
        await db.commit()
    return {"message": "deleted"}


# ── HTML builder (used by email_service) ──────────────────────────
def build_signature_html(sig: Signature) -> str:
    """Build email signature HTML — mirrors frontend buildPreviewHtml exactly."""
    if not sig:
        return ""
    color = sig.brand_color or "#1C305E"
    social = sig.social_links or {}

    html = f'<div style="margin-top:24px;padding-top:14px;border-top:2px solid {color};font-family:Arial,sans-serif;max-width:560px">'

    def _details_html():
        """All contact details: name, title, company, phone, email, website, addresses, footer."""
        d = ''
        if sig.full_name:  d += f'<div style="font-size:16px;font-weight:700;color:{color};margin:0 0 1px">{sig.full_name}</div>'
        if sig.title:      d += f'<div style="font-size:12px;color:#555555;margin:0 0 1px">{sig.title}</div>'
        if sig.company:    d += f'<div style="font-size:12px;font-weight:600;color:#333333;margin:0 0 6px">{sig.company}</div>'
        if sig.phone:      d += f'<div style="font-size:12px;color:#444444;margin:2px 0">&#128222; <a href="tel:{sig.phone}" style="color:#444444;text-decoration:none">{sig.phone}</a></div>'
        if sig.email_addr: d += f'<div style="font-size:12px;color:#444444;margin:2px 0">&#128231; <a href="mailto:{sig.email_addr}" style="color:{color};text-decoration:none">{sig.email_addr}</a></div>'
        if sig.website:    d += f'<div style="font-size:12px;color:#444444;margin:2px 0">&#127759; <a href="https://{sig.website}" style="color:{color};text-decoration:none">{sig.website}</a></div>'
        for label, addr in [("Mumbai", sig.address_mumbai), ("Delhi", sig.address_delhi), ("London", sig.address_london)]:
            if addr:
                d += f'<div style="font-size:11px;color:#666666;margin:2px 0">&#128205; <strong>{label}:</strong> {addr}</div>'
        footer = []
        if sig.cin:            footer.append(f"CIN: {sig.cin}")
        if sig.copyright_text: footer.append(sig.copyright_text)
        if footer:
            d += f'<div style="font-size:10px;color:#999999;margin:5px 0 0">{" &nbsp;&bull;&nbsp; ".join(footer)}</div>'
        return d

    if sig.logo_url:
        # Logo left, all details in right column — same layout as frontend preview
        html += '<table style="border:none!important;border-collapse:collapse;margin:0 0 6px 0;width:auto"><tr>'
        html += f'<td style="border:none!important;vertical-align:top;padding:0 14px 0 0;background:transparent!important"><img src="{sig.logo_url}" alt="{sig.company or ""}" style="height:60px;width:auto;border-radius:6px;display:block" /></td>'
        html += f'<td style="border:none!important;vertical-align:top;padding:0;background:transparent!important">{_details_html()}</td>'
        html += '</tr></table>'
    else:
        html += _details_html()

    # Social buttons
    btns = []
    wa_num = (social.get("whatsapp_number") or "").replace(" ", "").replace("+", "").replace("-", "")
    if wa_num:
        btns.append(f'<a href="https://wa.me/{wa_num}" title="WhatsApp" style="display:inline-block;margin-right:8px;text-decoration:none"><img src="https://img.icons8.com/ios-filled/50/666666/whatsapp--v1.png" width="16" height="16" alt="WhatsApp" style="display:block;border:none;border-radius:50%;background-color:#f5f5f5;padding:8px;" /></a>')

    SOCIAL_CFG = [
        ("linkedin",  "LinkedIn",  "https://img.icons8.com/ios-filled/50/666666/linkedin.png"),
        ("location",  "Location",  "https://img.icons8.com/ios-filled/50/666666/marker.png"),
        ("twitter",   "X",         "https://img.icons8.com/ios-filled/50/666666/twitterx--v1.png"),
        ("instagram", "Instagram", "https://img.icons8.com/ios-filled/50/666666/instagram-new.png"),
        ("facebook",  "Facebook",  "https://img.icons8.com/ios-filled/50/666666/facebook-new.png"),
    ]
    for key, label, src in SOCIAL_CFG:
        url = social.get(key, "")
        if url:
            btns.append(f'<a href="{url}" title="{label}" style="display:inline-block;margin-right:8px;text-decoration:none"><img src="{src}" width="16" height="16" alt="{label}" style="display:block;border:none;border-radius:50%;background-color:#f5f5f5;padding:8px;" /></a>')

    if btns:
        html += f'<div style="margin-top:10px">{"".join(btns)}</div>'

    html += '</div>'
    return html


async def get_user_signature_html(user_id: int, db: AsyncSession) -> str:
    result = await db.execute(
        select(Signature).where(
            Signature.user_id == user_id,
            Signature.is_default == True,
        )
    )
    sig = result.scalar_one_or_none()
    return build_signature_html(sig) if sig else ""
