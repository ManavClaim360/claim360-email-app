from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Optional
import os, uuid, shutil

from core.database import get_db
from core.auth import get_current_user, get_current_admin
from models.user import Template, Attachment, TemplateAttachment, User
from core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/templates", tags=["templates"])


class TemplateCreate(BaseModel):
    name: str
    subject: str
    body_html: str
    body_text: Optional[str] = ""
    variables: Optional[List[str]] = []
    is_shared: Optional[bool] = False
    attachment_ids: Optional[List[int]] = []


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    variables: Optional[List[str]] = None
    is_shared: Optional[bool] = None
    attachment_ids: Optional[List[int]] = None


class AttachmentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    is_shared: bool

    class Config:
        from_attributes = True


class TemplateResponse(BaseModel):
    id: int
    name: str
    subject: str
    body_html: str
    body_text: Optional[str]
    variables: List[str]
    is_shared: bool
    creator_id: int
    attachments: List[AttachmentResponse] = []

    class Config:
        from_attributes = True


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Template)
        .options(selectinload(Template.attachments).selectinload(TemplateAttachment.attachment))
        .where(
            (Template.creator_id == current_user.id) | (Template.is_shared == True)
        )
        .order_by(Template.created_at.desc())
    )
    templates = result.scalars().all()
    
    out = []
    for t in templates:
        atts = [ta.attachment for ta in t.attachments if ta.attachment]
        out.append(TemplateResponse(
            id=t.id, name=t.name, subject=t.subject,
            body_html=t.body_html, body_text=t.body_text,
            variables=t.variables or [], is_shared=t.is_shared,
            creator_id=t.creator_id,
            attachments=[AttachmentResponse(
                id=a.id, filename=a.filename, original_filename=a.original_filename,
                file_size=a.file_size, mime_type=a.mime_type, is_shared=a.is_shared
            ) for a in atts]
        ))
    return out


@router.post("/", response_model=TemplateResponse)
async def create_template(
    data: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    template = Template(
        name=data.name,
        subject=data.subject,
        body_html=data.body_html,
        body_text=data.body_text or "",
        variables=data.variables or [],
        is_shared=data.is_shared if current_user.is_admin else False,
        creator_id=current_user.id,
    )
    db.add(template)
    await db.flush()

    # Link attachments
    for att_id in (data.attachment_ids or []):
        ta = TemplateAttachment(template_id=template.id, attachment_id=att_id)
        db.add(ta)

    await db.commit()
    await db.refresh(template)
    return await _template_response(template, db)


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    for field, value in data.dict(exclude_none=True, exclude={"attachment_ids"}).items():
        setattr(template, field, value)

    if data.attachment_ids is not None:
        await db.execute(delete(TemplateAttachment).where(TemplateAttachment.template_id == template_id))
        for att_id in data.attachment_ids:
            ta = TemplateAttachment(template_id=template_id, attachment_id=att_id)
            db.add(ta)

    await db.commit()
    await db.refresh(template)
    return await _template_response(template, db)


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if template.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.delete(template)
    await db.commit()
    return {"message": "Deleted"}


# ── Attachments ──────────────────────────────────────────────
@router.post("/attachments/upload", response_model=AttachmentResponse)
async def upload_attachment(
    file: UploadFile = File(...),
    is_shared: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.size and file.size > settings.MAX_ATTACHMENT_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_ATTACHMENT_SIZE_MB}MB limit")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    stored_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, stored_name)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = os.path.getsize(file_path)
    import mimetypes
    mime = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"

    att = Attachment(
        filename=stored_name,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime,
        is_shared=is_shared and current_user.is_admin,
        uploaded_by=current_user.id,
    )
    db.add(att)
    await db.commit()
    await db.refresh(att)
    return AttachmentResponse(
        id=att.id, filename=att.filename, original_filename=att.original_filename,
        file_size=att.file_size, mime_type=att.mime_type, is_shared=att.is_shared
    )


@router.get("/attachments/", response_model=List[AttachmentResponse])
async def list_attachments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Attachment).where(
            (Attachment.uploaded_by == current_user.id) | (Attachment.is_shared == True)
        ).order_by(Attachment.created_at.desc())
    )
    atts = result.scalars().all()
    return [AttachmentResponse(
        id=a.id, filename=a.filename, original_filename=a.original_filename,
        file_size=a.file_size, mime_type=a.mime_type, is_shared=a.is_shared
    ) for a in atts]


@router.delete("/attachments/{att_id}")
async def delete_attachment(
    att_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Attachment).where(Attachment.id == att_id))
    att = result.scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=404, detail="Not found")
    if att.uploaded_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    if os.path.exists(att.file_path):
        os.remove(att.file_path)
    await db.delete(att)
    await db.commit()
    return {"message": "Deleted"}


async def _template_response(template: Template, db: AsyncSession) -> TemplateResponse:
    result = await db.execute(
        select(TemplateAttachment)
        .options(selectinload(TemplateAttachment.attachment))
        .where(TemplateAttachment.template_id == template.id)
    )
    tas = result.scalars().all()
    atts = [ta.attachment for ta in tas if ta.attachment]
    return TemplateResponse(
        id=template.id, name=template.name, subject=template.subject,
        body_html=template.body_html, body_text=template.body_text,
        variables=template.variables or [], is_shared=template.is_shared,
        creator_id=template.creator_id,
        attachments=[AttachmentResponse(
            id=a.id, filename=a.filename, original_filename=a.original_filename,
            file_size=a.file_size, mime_type=a.mime_type, is_shared=a.is_shared
        ) for a in atts]
    )
