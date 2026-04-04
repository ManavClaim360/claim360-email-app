from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Request, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json

from core.database import get_db, AsyncSessionLocal
from core.auth import get_current_user
from models.user import Campaign, Contact, CustomVariable, EmailLog, User, EmailStatus
from services.email_service import send_campaign
from core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


class ContactData(BaseModel):
    email: str
    cc_emails: Optional[List[str]] = []
    variables: Optional[Dict[str, Any]] = {}


class CampaignCreate(BaseModel):
    name: str
    template_id: Optional[int] = None
    contacts: List[ContactData]
    variable_names: Optional[List[str]] = []
    extra_attachment_ids: Optional[List[int]] = []


class CampaignResponse(BaseModel):
    id: int
    name: str
    status: str
    total_emails: int
    sent_count: int
    failed_count: int
    opened_count: int
    template_id: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


class EmailLogResponse(BaseModel):
    id: int
    recipient_email: str
    cc_emails: List[str]
    subject: Optional[str]
    status: str
    error_message: Optional[str]
    sent_at: Optional[str]
    opened_at: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Campaign).where(Campaign.name == data.name, Campaign.user_id == current_user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Campaign name already exists")

    campaign = Campaign(
        name=data.name,
        user_id=current_user.id,
        template_id=data.template_id,
        status="draft",
        total_emails=len(data.contacts),
        sent_count=0,
        failed_count=0,
        opened_count=0,
        extra_attachments=data.extra_attachment_ids or [],
    )
    db.add(campaign)
    await db.flush()

    # Add variables
    for var_name in (data.variable_names or []):
        v = CustomVariable(user_id=current_user.id, campaign_id=campaign.id, name=var_name)
        db.add(v)

    # Add contacts
    for c in data.contacts:
        contact = Contact(
            campaign_id=campaign.id,
            email=c.email,
            cc_emails=c.cc_emails or [],
            variables=c.variables or {},
        )
        db.add(contact)

    await db.commit()
    await db.refresh(campaign)

    return CampaignResponse(
        id=campaign.id, name=campaign.name, status=campaign.status,
        total_emails=campaign.total_emails, sent_count=campaign.sent_count,
        failed_count=campaign.failed_count, opened_count=campaign.opened_count,
        template_id=campaign.template_id,
        created_at=str(campaign.created_at),
    )


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign)
        .where(Campaign.user_id == current_user.id)
        .order_by(Campaign.created_at.desc())
    )
    campaigns = result.scalars().all()
    return [CampaignResponse(
        id=c.id, name=c.name, status=c.status,
        total_emails=c.total_emails, sent_count=c.sent_count,
        failed_count=c.failed_count, opened_count=c.opened_count,
        template_id=c.template_id, created_at=str(c.created_at),
    ) for c in campaigns]


@router.get("/{campaign_id}/logs", response_model=List[EmailLogResponse])
async def get_campaign_logs(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    # Verify ownership
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign or (campaign.user_id != current_user.id and not current_user.is_admin):
        raise HTTPException(status_code=404, detail="Campaign not found")

    offset = (page - 1) * page_size
    result = await db.execute(
        select(EmailLog)
        .where(EmailLog.campaign_id == campaign_id)
        .order_by(EmailLog.created_at)
        .offset(offset)
        .limit(page_size)
    )
    logs = result.scalars().all()
    return [EmailLogResponse(
        id=l.id, recipient_email=l.recipient_email,
        cc_emails=l.cc_emails or [], subject=l.subject,
        status=l.status.value if hasattr(l.status, 'value') else l.status,
        error_message=l.error_message,
        sent_at=str(l.sent_at) if l.sent_at else None,
        opened_at=str(l.opened_at) if l.opened_at else None,
    ) for l in logs]


@router.get("/opens/all")
async def get_all_opens(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all opened email logs across all campaigns for this user, newest first."""
    result = await db.execute(
        select(EmailLog, Campaign.name)
        .join(Campaign, EmailLog.campaign_id == Campaign.id)
        .where(
            Campaign.user_id == current_user.id,
            EmailLog.opened_at.isnot(None),
        )
        .order_by(EmailLog.opened_at.desc())
        .limit(500)
    )
    rows = result.all()
    return [
        {
            "id": log.id,
            "recipient_email": log.recipient_email,
            "campaign_name": name,
            "opened_at": str(log.opened_at),
            "subject": log.subject,
        }
        for log, name in rows
    ]



async def start_campaign(
    campaign_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status == "running":
        raise HTTPException(status_code=400, detail="Campaign is already running")

    base_url = str(request.base_url).rstrip("/")
    background_tasks.add_task(_run_campaign, campaign_id, base_url)
    return {"message": "Campaign started", "campaign_id": campaign_id}

async def _run_campaign(campaign_id: int, base_url: str = None):
    """Background task to run campaign — runs in FastAPI background task."""
    import traceback
    from core.database import AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as db:
            result = await send_campaign(campaign_id, db, base_url=base_url)
            print(f"Campaign {campaign_id} finished: {result}")
    except Exception as exc:
        print(f"Campaign {campaign_id} CRASHED: {exc}")
        traceback.print_exc()
        # Mark campaign failed
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                from models.user import Campaign
                res = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
                camp = res.scalar_one_or_none()
                if camp:
                    camp.status = "failed"
                    await db.commit()
        except Exception:
            pass


@router.get("/{campaign_id}/stream")
async def stream_campaign_progress(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify ownership once before starting the stream
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign_check = result.scalar_one_or_none()
    if not campaign_check or (campaign_check.user_id != current_user.id and not current_user.is_admin):
        raise HTTPException(status_code=404, detail="Campaign not found")

    async def event_generator():
        # Use a dedicated session for the long-lived SSE stream
        # (the request-scoped session from get_db is closed after the handler returns)
        async with AsyncSessionLocal() as stream_db:
            while True:
                result = await stream_db.execute(
                    select(Campaign).where(Campaign.id == campaign_id)
                )
                campaign = result.scalar_one_or_none()
                if not campaign:
                    break

                logs_result = await stream_db.execute(
                    select(EmailLog)
                    .where(EmailLog.campaign_id == campaign_id)
                    .order_by(EmailLog.created_at.desc())
                    .limit(50)
                )
                logs = logs_result.scalars().all()

                data = {
                    "status": campaign.status,
                    "total": campaign.total_emails,
                    "sent": campaign.sent_count,
                    "failed": campaign.failed_count,
                    "opened": campaign.opened_count,
                    "logs": [
                        {
                            "id": l.id,
                            "email": l.recipient_email,
                            "status": l.status.value if hasattr(l.status, 'value') else l.status,
                            "sent_at": str(l.sent_at) if l.sent_at else None,
                        }
                        for l in logs
                    ]
                }
                yield f"data: {json.dumps(data)}\n\n"

                if campaign.status in ("completed", "failed"):
                    break
                await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign or (campaign.user_id != current_user.id and not current_user.is_admin):
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(campaign)
    await db.commit()
    return {"message": "Deleted"}
