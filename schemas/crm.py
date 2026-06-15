from datetime import datetime
from typing import Any
from pydantic import BaseModel


# ─────────────────────────────────────────
# CHAT CON EL AGENTE CRM
# ─────────────────────────────────────────

class CRMChatRequest(BaseModel):
    message: str


class CRMChatResponse(BaseModel):
    reply: str
    session_state: dict[str, Any] = {}
    tool_calls: list[dict[str, Any]] = []
    blocked: bool = False


# ─────────────────────────────────────────
# CLIENTES
# ─────────────────────────────────────────

class CustomerResponse(BaseModel):
    id: int
    name: str
    company: str | None
    email: str | None
    phone: str | None
    industry: str | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerListResponse(BaseModel):
    customers: list[CustomerResponse]
    total: int


# ─────────────────────────────────────────
# PRODUCTOS
# ─────────────────────────────────────────

class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    description: str | None
    unit_price: float
    category: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    products: list[ProductResponse]
    total: int


# ─────────────────────────────────────────
# OPORTUNIDADES
# ─────────────────────────────────────────

class OpportunityItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float

    model_config = {"from_attributes": True}


class OpportunityResponse(BaseModel):
    id: int
    customer_id: int
    created_by_id: int | None
    name: str
    stage: str
    total_amount: float
    discount_pct: float
    notes: str | None
    items: list[OpportunityItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OpportunityListResponse(BaseModel):
    opportunities: list[OpportunityResponse]
    total: int
