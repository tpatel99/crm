from datetime import datetime, date

from sqlalchemy import ForeignKey, String, Text, Numeric, Date, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

STAGES = ["Lead", "Qualified", "Proposal", "Negotiation", "Won", "Lost"]
# Default win probability per stage, used for weighted forecast
STAGE_PROB = {"Lead": 0.1, "Qualified": 0.25, "Proposal": 0.5, "Negotiation": 0.75, "Won": 1.0, "Lost": 0.0}


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    website: Mapped[str] = mapped_column(String(255), default="")
    industry: Mapped[str] = mapped_column(String(120), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    contacts: Mapped[list["Contact"]] = relationship(back_populates="company")
    deals: Mapped[list["Deal"]] = relationship(back_populates="company")


class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str] = mapped_column(String(120), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(60), default="")
    title: Mapped[str] = mapped_column(String(120), default="")
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    company: Mapped[Company | None] = relationship(back_populates="contacts")


class Deal(Base):
    __tablename__ = "deals"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    value: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    stage: Mapped[str] = mapped_column(String(40), default="Lead")
    expected_close: Mapped[date | None] = mapped_column(Date)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id"))
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)
    company: Mapped[Company | None] = relationship(back_populates="deals")


class Activity(Base):
    """Calls, emails, meetings and notes logged against a deal/contact/company."""
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), default="note")  # note|call|email|meeting
    body: Mapped[str] = mapped_column(Text, default="")
    deal_id: Mapped[int | None] = mapped_column(ForeignKey("deals.id"))
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id"))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    due_date: Mapped[date | None] = mapped_column(Date)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    deal_id: Mapped[int | None] = mapped_column(ForeignKey("deals.id"))
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id"))
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
