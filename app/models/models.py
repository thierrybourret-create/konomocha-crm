from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Numeric, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    agent = "agent"

class PipelineStatus(str, enum.Enum):
    awaiting_feedback = "Awaiting Feedback"
    awaiting_info     = "Awaiting Info"
    awaiting_samples  = "Awaiting Samples"
    cancelled         = "Cancelled"
    catalogue_sent    = "Catalogue Sent"
    closed            = "Closed / No Action"
    deposit_paid      = "Deposit Paid"
    form_completed    = "Form Completed"
    in_progress       = "In Progress"
    on_hold           = "On Hold"
    order_placed      = "Order Placed"
    price_list_sent   = "Price List Sent"
    pricing_sent      = "Pricing Sent"
    quotation_sent    = "Quotation Sent"
    samples_delivered = "Samples Delivered"
    samples_requested = "Samples Requested"
    samples_sent      = "Samples Sent"
    stalled           = "Stalled"

class EmailDirection(str, enum.Enum):
    inbound  = "inbound"
    outbound = "outbound"
class CRMRole(Base):
    __tablename__ = "crm_roles"
    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(100), nullable=False, unique=True)
    page_access  = Column(Text, nullable=True)
    report_access= Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    users        = relationship("User", back_populates="crm_role")

class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(SAEnum(UserRole), default=UserRole.agent, nullable=False)
    is_active       = Column(Boolean, default=True)
    page_access     = Column(Text, nullable=True)
    role_id         = Column(Integer, ForeignKey("crm_roles.id"), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    pipeline_entries = relationship("PipelineEntry", back_populates="owner")
    crm_role         = relationship("CRMRole", back_populates="users", foreign_keys=[role_id])
    email_logs       = relationship("EmailLog", back_populates="logged_by")

class Contact(Base):
    __tablename__ = "contacts"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(255), nullable=False)
    company    = Column(String(255), index=True)
    email      = Column(String(255), index=True)
    phone      = Column(String(50))
    job_title  = Column(String(255))
    country    = Column(String(100))
    address    = Column(Text)
    tags       = Column(String(500))
    notes      = Column(Text)
    source     = Column(String(50), default="manual")
    owner_id   = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, default=None)
    owner            = relationship("User", foreign_keys=[owner_id])
    pipeline_entries = relationship("PipelineEntry", back_populates="contact")
    email_logs       = relationship("EmailLog", back_populates="contact")
    orders           = relationship("Order", back_populates="contact")
    contact_notes    = relationship("ContactNote", back_populates="contact", order_by="ContactNote.created_at")
    attachments      = relationship("ContactAttachment", back_populates="contact", order_by="ContactAttachment.created_at")
    tasks            = relationship("ContactTask", back_populates="contact", order_by="ContactTask.created_at")

class Brand(Base):
    __tablename__ = "brands"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(255), unique=True, nullable=False)
    notes      = Column(Text)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    pipeline_entries = relationship("PipelineEntry", back_populates="brand")
    orders           = relationship("Order", back_populates="brand")
class PipelineEntry(Base):
    __tablename__ = "pipeline_entries"
    id              = Column(Integer, primary_key=True, index=True)
    contact_id      = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    brand_id        = Column(Integer, ForeignKey("brands.id"), nullable=False)
    status          = Column(String(100), nullable=False, default="In Progress")
    potential_value = Column(Numeric(12, 2), nullable=False)
    next_action     = Column(Text)
    fob_date        = Column(Date)
    owner_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes           = Column(Text)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at      = Column(DateTime(timezone=True), nullable=True, default=None)
    close_reason    = Column(String(500), nullable=True)
    closed_at       = Column(DateTime(timezone=True), nullable=True)
    contact     = relationship("Contact", back_populates="pipeline_entries")
    brand       = relationship("Brand",   back_populates="pipeline_entries")
    owner       = relationship("User",    back_populates="pipeline_entries")
    notes_list  = relationship("PipelineNote", back_populates="pipeline_entry", order_by="PipelineNote.created_at")

class EmailLog(Base):
    __tablename__ = "email_logs"
    id             = Column(Integer, primary_key=True, index=True)
    contact_id     = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    direction      = Column(SAEnum(EmailDirection), nullable=False)
    sent_at        = Column(DateTime(timezone=True), nullable=False)
    subject        = Column(String(500))
    body_snippet   = Column(Text)
    from_address   = Column(String(255))
    to_address     = Column(String(255))
    raw_message_id = Column(String(255))
    bcc_address    = Column(String(255))
    logged_by_id   = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    contact   = relationship("Contact", back_populates="email_logs")
    logged_by = relationship("User",    back_populates="email_logs")

class Order(Base):
    __tablename__ = "orders"
    id                     = Column(Integer, primary_key=True, index=True)
    contact_id             = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    brand_id               = Column(Integer, ForeignKey("brands.id"), nullable=False)
    order_date             = Column(Date, nullable=False)
    order_value            = Column(Numeric(12, 2), nullable=False)
    currency               = Column(String(3), default="USD")
    po_date                = Column(Date)
    pi_date                = Column(Date)
    deposit_date           = Column(Date)
    fob_date               = Column(Date)
    payment_date           = Column(Date)
    gross_commission_rate  = Column(Numeric(12, 2), default=0)
    testing_cost_deduction = Column(Numeric(12, 2), default=0)
    net_commission         = Column(Numeric(12, 2))
    status                 = Column(String(100), default="PO Received")
    notes                  = Column(Text)
    created_at             = Column(DateTime(timezone=True), server_default=func.now())
    updated_at             = Column(DateTime(timezone=True), onupdate=func.now())
    ship_date              = Column(Date)
    fully_paid_date        = Column(Date)
    commission_invoiced_date = Column(Date)
    commission_paid_date   = Column(Date)
    bonus_paid_date        = Column(Date)
    bonus_amount           = Column(Numeric(12, 2))
    owner_id               = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_at             = Column(DateTime(timezone=True), nullable=True, default=None)
    contact  = relationship("Contact", back_populates="orders")
    brand    = relationship("Brand",   back_populates="orders")
    owner    = relationship("User",    foreign_keys=[owner_id])

class ContactNote(Base):
    __tablename__ = "contact_notes"
    id         = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    body       = Column(Text, nullable=False)
    author_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, default=None)
    contact = relationship("Contact", back_populates="contact_notes")
    author  = relationship("User")

class ContactAttachment(Base):
    __tablename__ = "contact_attachments"
    id             = Column(Integer, primary_key=True, index=True)
    contact_id     = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    filename       = Column(String(500), nullable=False)
    stored_name    = Column(String(500), nullable=False)
    file_size      = Column(Integer)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    contact     = relationship("Contact", back_populates="attachments")
    uploaded_by = relationship("User")

class ContactTask(Base):
    __tablename__ = "contact_tasks"
    id             = Column(Integer, primary_key=True, index=True)
    contact_id     = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    title          = Column(String(500), nullable=False)
    due_date       = Column(Date, nullable=True)
    completed      = Column(Boolean, default=False)
    completed_at   = Column(DateTime(timezone=True), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    contact     = relationship("Contact", back_populates="tasks")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    created_by  = relationship("User", foreign_keys=[created_by_id])

class PipelineNote(Base):
    __tablename__ = "pipeline_notes"
    id              = Column(Integer, primary_key=True, index=True)
    pipeline_id     = Column(Integer, ForeignKey("pipeline_entries.id"), nullable=False)
    body            = Column(Text, nullable=False)
    author_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), nullable=True)
    updated_by_id   = Column(Integer, ForeignKey("users.id"), nullable=True)
    deleted_at      = Column(DateTime(timezone=True), nullable=True, default=None)
    pipeline_entry = relationship("PipelineEntry", back_populates="notes_list")
    author         = relationship("User", foreign_keys=[author_id])
    updated_by     = relationship("User", foreign_keys=[updated_by_id])


class AppStage(Base):
    __tablename__ = 'app_stages'
    id          = Column(Integer, primary_key=True)
    stage_type  = Column(String, nullable=False)   # 'pipeline' or 'order'
    name        = Column(String, nullable=False)   # internal key
    label       = Column(String, nullable=False)   # display label
    probability = Column(Integer, nullable=True)   # 0-100, null for order stages
    position    = Column(Integer, nullable=False, default=0)


class AuditLog(Base):
    __tablename__ = 'audit_log'
    id           = Column(Integer, primary_key=True)
    entity_type  = Column(String(50),  nullable=False)   # 'pipeline' | 'order'
    entity_id    = Column(Integer,     nullable=False)
    contact_name = Column(String(500), nullable=True)    # denormalized at log time
    brand_name   = Column(String(255), nullable=True)    # denormalized at log time
    action       = Column(String(50),  nullable=False)   # 'created' | 'updated' | 'deleted'
    field_name   = Column(String(100), nullable=True)    # which field changed
    old_value    = Column(Text,        nullable=True)
    new_value    = Column(Text,        nullable=True)
    user_id      = Column(Integer,     nullable=True)
    user_name    = Column(String(200), nullable=True)    # denormalized
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
