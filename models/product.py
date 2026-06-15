from sqlalchemy import String, Numeric, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.db import Base


class Product(Base):
    __tablename__ = "crm_products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    sku: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    opportunity_items = relationship("OpportunityItem", back_populates="product", cascade="all, delete-orphan")
