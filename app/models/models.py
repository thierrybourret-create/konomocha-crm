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

class OrderStatus(str, enum.Enum):
    confirmed = "Confirmed"
    invoiced  = "Invoiced"
    paid      = "Paid"

class EmailDirection(str, enum.Enum):
    inbound  = "inbound"
    outbound = "outbound"
class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(SAEnum(UserRole), default=UserRole.agent, nullable=False)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    pipeline_entries = relationship("PipelineEntry", back_populates="owner")
    email_logs       = relationship("EmailLog", back_populates="logged_by")

class Contact(Base):
    __tablename__ = "contacts"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(255), nullable=False)
    company    = Column(String(255), index=True)
    email      = Column(String(255), index=True)
    phone      = Column(String(50))
    country    = Column(String(100))
    address    = Column(Text)
    tags       = Column(String(500))
    notes      = Column(Text)
    source     = Column(String(50), default="manual")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    pipeline_entries = relationship("PipelineEntry", back_populates="contact")
    email_logs       = relationship("EmailLog", back_populates="contact")
    orders           = relationship("Order", back_populates="contact")

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
    status          = Column(String(100), nullable=False, default=In Progress)
    potential_value = Column(Numeric(12, 2), nullable=False)
    next_action     = Column(Text)
    due_date        = Column(Date)
    owner_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes           = Column(Text)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    contact = relationship("Contact", back_populates="pipeline_entries")
    brand   = relationship("Brand",   back_populates="pipeline_entries")
    owner   = relationship("User",    back_populates="pipeline_entries")

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
    gross_commission_rate  = Column(Numeric(5, 2), nullable=False)
    testing_cost_deduction = Column(Numeric(12, 2), default=0)
    net_commission         = Column(Numeric(12, 2))
    status                 = Column(SAEnum(OrderStatus), default=OrderStatus.confirmed)
    notes                  = Column(Text)
    created_at             = Column(DateTime(timezone=True), server_default=func.now())
    updated_at             = Column(DateTime(timezone=True), onupdate=func.now())
    contact = relationship("Contact", back_populates="orders")
    brand   = relationship("Brand",   back_populates="orders")
