from sqlalchemy import String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.db import Base


class Meeting(Base):
    __tablename__ = "crm_meetings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("crm_customers.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    opportunity_id: Mapped[int | None] = mapped_column(
        ForeignKey("crm_opportunities.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    scheduled_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # "scheduled" | "completed" | "cancelled"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("Customer", back_populates="meetings")
    opportunity = relationship("Opportunity", back_populates="meetings")
    created_by = relationship("User")
