from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float,
    ForeignKey, JSON, Enum as SAEnum, BigInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import enum


class EmailStatus(str, enum.Enum):
    pending = "pending"
    sending = "sending"
    sent = "sent"
    failed = "failed"
    opened = "opened"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    oauth_tokens = relationship("OAuthToken", back_populates="user", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="creator")
    campaigns = relationship("Campaign", back_populates="user")
    email_logs = relationship("EmailLog", back_populates="user")


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    gmail_email = Column(String(255), nullable=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime(timezone=True), nullable=True)
    scopes = Column(JSON, nullable=True)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="oauth_tokens")


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)
    variables = Column(JSON, default=list)  # list of variable names used
    is_shared = Column(Boolean, default=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    creator = relationship("User", back_populates="templates")
    attachments = relationship("TemplateAttachment", back_populates="template", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="template")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    is_shared = Column(Boolean, default=False)  # admin-shared
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    uploader = relationship("User")
    template_attachments = relationship("TemplateAttachment", back_populates="attachment")


class TemplateAttachment(Base):
    __tablename__ = "template_attachments"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    attachment_id = Column(Integer, ForeignKey("attachments.id", ondelete="CASCADE"), nullable=False)
    is_required = Column(Boolean, default=False)  # admin can mark required
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("Template", back_populates="attachments")
    attachment = relationship("Attachment", back_populates="template_attachments")


class CustomVariable(Base):
    __tablename__ = "custom_variables"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=False)  # e.g. "name", "company"
    display_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    campaign = relationship("Campaign", back_populates="variables")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    cc_emails = Column(JSON, default=list)
    variables = Column(JSON, default=dict)  # {var_name: value}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    campaign = relationship("Campaign", back_populates="contacts")
    email_logs = relationship("EmailLog", back_populates="contact")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)
    status = Column(String(50), default="draft")  # draft, running, completed, failed
    total_emails = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    extra_attachments = Column(JSON, default=list)  # additional attachment IDs
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="campaigns")
    template = relationship("Template", back_populates="campaigns")
    contacts = relationship("Contact", back_populates="campaign", cascade="all, delete-orphan")
    variables = relationship("CustomVariable", back_populates="campaign", cascade="all, delete-orphan")
    email_logs = relationship("EmailLog", back_populates="campaign")


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    recipient_email = Column(String(255), nullable=False)
    cc_emails = Column(JSON, default=list)
    subject = Column(String(500), nullable=True)
    status = Column(SAEnum(EmailStatus), default=EmailStatus.pending)
    error_message = Column(Text, nullable=True)
    gmail_message_id = Column(String(255), nullable=True)
    tracking_id = Column(String(100), unique=True, nullable=True, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    campaign = relationship("Campaign", back_populates="email_logs")
    user = relationship("User", back_populates="email_logs")
    contact = relationship("Contact", back_populates="email_logs")
    tracking_events = relationship("TrackingData", back_populates="email_log")


class TrackingData(Base):
    __tablename__ = "tracking_data"

    id = Column(Integer, primary_key=True, index=True)
    email_log_id = Column(Integer, ForeignKey("email_logs.id"), nullable=False)
    tracking_id = Column(String(100), nullable=False, index=True)
    event_type = Column(String(50), default="open")  # open, click
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    email_log = relationship("EmailLog", back_populates="tracking_events")


class Signature(Base):
    __tablename__ = "signatures"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name        = Column(String(255), nullable=False, default="My Signature")
    is_default  = Column(Boolean, default=True)   # auto-append to every email
    is_shared   = Column(Boolean, default=False)  # admin can share as org template

    # Dynamic fields stored as JSON — each user fills their own values
    full_name   = Column(String(255), nullable=True)
    title       = Column(String(255), nullable=True)
    company     = Column(String(255), nullable=True, default="CLAIM 360")
    phone       = Column(String(100), nullable=True)
    website     = Column(String(255), nullable=True)
    email_addr  = Column(String(255), nullable=True)
    address_mumbai = Column(Text, nullable=True)
    address_delhi  = Column(Text, nullable=True)
    address_london = Column(Text, nullable=True)
    cin         = Column(String(100), nullable=True)
    copyright_text = Column(String(255), nullable=True)

    # Optional: logo URL (can be a hosted image URL)
    logo_url    = Column(Text, nullable=True)  # Text for base64 images
    # Social media links — stored as JSON {"whatsapp":"...","linkedin":"...","location":"..."}
    social_links = Column(JSON, nullable=True, default=dict)
    # Brand colour for the signature divider/name
    brand_color = Column(String(20), nullable=True, default="#1C305E")

    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")


class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    code = Column(String(10), nullable=False)
    purpose = Column(String(50), nullable=False)  # 'register', 'reset'
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OAuthState(Base):
    """CSRF state for OAuth login — avoids in-memory dicts."""
    __tablename__ = "oauth_states"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
