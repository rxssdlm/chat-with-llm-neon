from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.db import Base


class Opportunity(Base):
    __tablename__ = "crm_opportunities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("crm_customers.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # "prospecting" | "qualification" | "proposal" | "negotiation" | "closed_won" | "closed_lost"
    stage: Mapped[str] = mapped_column(String(30), nullable=False, default="prospecting")

    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    discount_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("Customer", back_populates="opportunities")
    created_by = relationship("User")
    items = relationship("OpportunityItem", back_populates="opportunity", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="opportunity")


class OpportunityItem(Base):
    __tablename__ = "crm_opportunity_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey("crm_opportunities.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("crm_products.id", ondelete="RESTRICT"), nullable=False, index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    opportunity = relationship("Opportunity", back_populates="items")
    product = relationship("Product", back_populates="opportunity_items")
