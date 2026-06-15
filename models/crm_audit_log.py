from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.db import Base


class CRMAuditLog(Base):
    __tablename__ = "crm_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # "tool_call" | "security_block" | "error"
    event_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)

    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
