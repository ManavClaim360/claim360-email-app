import re
import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.user import Campaign, EmailLog, Contact, Attachment, EmailStatus, OAuthToken, TrackingData, TemplateAttachment
from services.gmail_service import get_credentials, build_email_message
from core.config import get_settings
from googleapiclient.discovery import build
from api.signature import get_user_signature_html

settings = get_settings()


def sanitize_variable_spans(html: str) -> str:
    """
    Remove editor-only styled <span> wrappers around {{variables}},
    keeping the plain {{variable}} text so substitution works correctly.
    r'\\1' keeps the captured group — the {{var}} text itself.
    """
    if not html:
        return html
    # <span data-var="name" ...>{{name}}</span>  →  {{name}}
    html = re.sub(
        r'<span[^>]*data-var="[^"]*"[^>]*>\s*(\{\{[^}]+\}\})\s*</span>',
        r'\1', html
    )
    # <span contenteditable="false" ...>{{name}}</span>  →  {{name}}
    html = re.sub(
        r'<span[^>]*contenteditable=["\']false["\'][^>]*>(\{\{[^}]+\}\})</span>',
        r'\1', html
    )
    # Any background/border styled span wrapping {{var}}  →  {{var}}
    html = re.sub(
        r'<span[^>]*style="[^"]*(?:background|border)[^"]*"[^>]*>(\{\{[^}]+\}\})</span>',
        r'\1', html
    )
    return html


def substitute_variables(template: str, variables: Dict[str, str]) -> str:
    """Replace {{variable}} placeholders with actual values, handling edge cases."""
    if not template:
        return ""
    
    def replacer(match):
        key = match.group(1).strip()
        # Fallback to the original placeholder if variable not found
        val = variables.get(key)
        if val is None:
            return match.group(0)
        
        # Ensure value is stringified, handle None or shared data
        val_str = str(val)
        
        # If it looks like HTML, we don't escape (since we are in HTML body)
        # But for plain text fields, we might need caution.
        return val_str

    # Support {{ var }}, {{var}}, and spaces inside
    return re.sub(r'\{\{\s*(\w+)\s*\}\}', replacer, template)


def generate_tracking_id() -> str:
    return str(uuid.uuid4()).replace("-", "")


def _send_via_gmail_sync(creds, raw_message: str) -> str:
    """Synchronous Gmail API send — safe to run in thread executor."""
    service = build("gmail", "v1", credentials=creds)
    result = service.users().messages().send(
        userId="me", body={"raw": raw_message}
    ).execute()
    return result.get("id", "")


async def send_campaign(campaign_id: int, db: AsyncSession, progress_callback=None, base_url: str = None):
    # ── Load campaign ─────────────────────────────────────────────
    result = await db.execute(
        select(Campaign)
        .options(
            selectinload(Campaign.template),
            selectinload(Campaign.contacts),
        )
        .where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        return {"error": "Campaign not found"}

    # ── Gmail credentials ─────────────────────────────────────────
    creds = await get_credentials(campaign.user_id, db)
    if not creds:
        campaign.status = "failed"
        await db.commit()
        return {"error": "No valid Gmail connection. Please reconnect OAuth."}

    # ── Sender email ──────────────────────────────────────────────
    tok_result = await db.execute(
        select(OAuthToken).where(
            OAuthToken.user_id == campaign.user_id,
            OAuthToken.is_valid == True
        )
    )
    oauth_token = tok_result.scalar_one_or_none()
    sender_email = oauth_token.gmail_email if oauth_token else ""

    # ── Template data ─────────────────────────────────────────────
    template = campaign.template
    subject_tpl   = template.subject    if template else "(no subject)"
    body_html_tpl = template.body_html  if template else ""
    body_text_tpl = (template.body_text or "") if template else ""

    # Sanitize any leftover editor spans from body_html
    import re
    body_html_tpl = sanitize_variable_spans(body_html_tpl)
    body_html_tpl = re.sub(r'<table\b([^>]*)>', r'<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; border: 1px solid #dddddd;" \1>', body_html_tpl, flags=re.IGNORECASE)
    body_html_tpl = re.sub(r'<td\b([^>]*)>', r'<td style="border: 1px solid #dddddd; padding: 6px;" \1>', body_html_tpl, flags=re.IGNORECASE)
    body_html_tpl = re.sub(r'<th\b([^>]*)>', r'<th style="border: 1px solid #dddddd; padding: 6px;" \1>', body_html_tpl, flags=re.IGNORECASE)

    # ── Signature ─────────────────────────────────────────────────
    sig_html = await get_user_signature_html(campaign.user_id, db)
    if sig_html:
        body_html_tpl += f'<br>{sig_html}'

    # ── Gather template attachments ───────────────────────────────
    template_attachments = []
    if template:
        ta_result = await db.execute(
            select(TemplateAttachment)
            .options(selectinload(TemplateAttachment.attachment))
            .where(TemplateAttachment.template_id == template.id)
        )
        for ta in ta_result.scalars().all():
            if ta.attachment:
                a = ta.attachment
                template_attachments.append({
                    "file_path": a.file_path,
                    "original_filename": a.original_filename,
                    "mime_type": a.mime_type,
                })

    for att_id in (campaign.extra_attachments or []):
        att_res = await db.execute(select(Attachment).where(Attachment.id == att_id))
        att = att_res.scalar_one_or_none()
        if att:
            template_attachments.append({
                "file_path": att.file_path,
                "original_filename": att.original_filename,
                "mime_type": att.mime_type,
            })

    # ── Mark campaign running ─────────────────────────────────────
    campaign.status = "running"
    campaign.started_at = datetime.now(timezone.utc)
    await db.commit()

    sent = 0
    failed = 0
    loop = asyncio.get_event_loop()

    for contact in campaign.contacts:
        tracking_id  = generate_tracking_id()
        actual_base = base_url or settings.BASE_URL
        tracking_url = f"{actual_base.rstrip('/')}/api/track/{tracking_id}/pixel.gif"
        vars_ = contact.variables or {}

        subject   = substitute_variables(subject_tpl,   vars_)
        body_html = substitute_variables(body_html_tpl, vars_)
        body_text = substitute_variables(body_text_tpl, vars_)

        log = EmailLog(
            campaign_id=campaign_id,
            user_id=campaign.user_id,
            contact_id=contact.id,
            recipient_email=contact.email,
            cc_emails=contact.cc_emails or [],
            subject=subject,
            status=EmailStatus.sending,
            tracking_id=tracking_id,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)

        if progress_callback:
            await progress_callback(log.id, "sending", contact.email)

        try:
            raw = build_email_message(
                sender=sender_email,
                to=[contact.email],
                cc=contact.cc_emails or [],
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                attachments=template_attachments,
                tracking_pixel_url=tracking_url,
            )

            msg_id = await loop.run_in_executor(
                None, _send_via_gmail_sync, creds, raw
            )

            log.status = EmailStatus.sent
            log.sent_at = datetime.now(timezone.utc)
            log.gmail_message_id = msg_id
            sent += 1

            if progress_callback:
                await progress_callback(log.id, "sent", contact.email)

        except Exception as exc:
            log.status = EmailStatus.failed
            log.error_message = str(exc)[:500]
            failed += 1
            if progress_callback:
                await progress_callback(log.id, "failed", f"{contact.email}: {exc}")

        await db.commit()
        await asyncio.sleep(settings.SEND_DELAY_SECONDS)

    campaign.status = "completed"
    campaign.sent_count = sent
    campaign.failed_count = failed
    campaign.completed_at = datetime.now(timezone.utc)
    await db.commit()

    return {"sent": sent, "failed": failed, "total": len(campaign.contacts)}


async def record_open(tracking_id: str, db: AsyncSession, ip: str = None, ua: str = None):
    result = await db.execute(
        select(EmailLog).where(EmailLog.tracking_id == tracking_id)
    )
    log = result.scalar_one_or_none()
    if not log:
        return

    is_first_open = log.opened_at is None
    if log.status in (EmailStatus.sent, EmailStatus.sending):
        log.status = EmailStatus.opened
    if is_first_open:
        log.opened_at = datetime.now(timezone.utc)

    event = TrackingData(
        email_log_id=log.id,
        tracking_id=tracking_id,
        event_type="open",
        ip_address=ip,
        user_agent=ua,
    )
    db.add(event)

    if is_first_open:
        camp_res = await db.execute(select(Campaign).where(Campaign.id == log.campaign_id))
        campaign = camp_res.scalar_one_or_none()
        if campaign:
            campaign.opened_count = (campaign.opened_count or 0) + 1

    await db.commit()


async def send_test_email(template_id: int, user_id: int, db: AsyncSession, to_email: str = None):
    """Send a single test email of a template to the user."""
    from models.user import Template, TemplateAttachment, OAuthToken
    from services.gmail_service import get_credentials, build_email_message
    from api.signature import get_user_signature_html
    import asyncio, re

    # ── Load template ─────────────────────────────────────────────
    result = await db.execute(
        select(Template)
        .options(selectinload(Template.attachments).selectinload(TemplateAttachment.attachment))
        .where(Template.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise ValueError("Template not found")

    # ── Gmail credentials ─────────────────────────────────────────
    creds = await get_credentials(user_id, db)
    if not creds:
        raise ValueError("No valid Gmail connection. Please connect Gmail first.")

    # ── Sender email ──────────────────────────────────────────────
    tok_result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.is_valid == True)
    )
    oauth_token = tok_result.scalar_one_or_none()
    sender_email = oauth_token.gmail_email if oauth_token else ""
    
    recipient = to_email or (oauth_token.gmail_email if oauth_token else None)
    if not recipient:
        raise ValueError("No recipient email found for test send.")

    # ── Template data ─────────────────────────────────────────────
    # Use dummy data for variables in test send
    dummy_vars = {v: f"[{v}]" for v in (template.variables or ["name", "company"])}
    
    subject = substitute_variables(template.subject, dummy_vars)
    body_html = substitute_variables(template.body_html, dummy_vars)
    body_text = substitute_variables(template.body_text or "", dummy_vars)
    
    # Sanitize and add signature
    body_html = sanitize_variable_spans(body_html)
    # Add borders to tables for test
    body_html = re.sub(r'<table\b([^>]*)>', r'<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; border: 1px solid #dddddd;" \1>', body_html, flags=re.IGNORECASE)
    
    sig_html = await get_user_signature_html(user_id, db)
    if sig_html:
        body_html += f'<br>{sig_html}'

    # ── Attachments ───────────────────────────────────────────────
    atts = []
    for ta in template.attachments:
        if ta.attachment:
            a = ta.attachment
            atts.append({
                "file_path": a.file_path,
                "original_filename": a.original_filename,
                "mime_type": a.mime_type,
            })

    # ── Build and send ────────────────────────────────────────────
    from services.gmail_service import build_email_message
    raw_message = build_email_message(
        sender=sender_email,
        to=[recipient],
        cc=[],
        subject=f"[TEST] {subject}",
        body_html=body_html,
        body_text=body_text,
        attachments=atts,
        tracking_pixel_url=None # No tracking for test sends
    )
    
    loop = asyncio.get_event_loop()
    msg_id = await loop.run_in_executor(None, _send_via_gmail_sync, creds, raw_message)
    return msg_id