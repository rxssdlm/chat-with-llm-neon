from sqlalchemy import String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.db import Base


class Customer(Base):
    __tablename__ = "crm_customers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    company: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    leads = relationship("Lead", back_populates="customer", cascade="all, delete-orphan")
    opportunities = relationship("Opportunity", back_populates="customer", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="customer", cascade="all, delete-orphan")
