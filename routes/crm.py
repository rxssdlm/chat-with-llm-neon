from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.agents.crm.agent import run_crm_agent
from core.agents.crm.security import detect_prompt_injection
from core.db import get_db, get_database_url
from core.deps import get_current_user
from models.user import User
from models.customer import Customer
from models.product import Product
from models.opportunity import Opportunity
from models.crm_audit_log import CRMAuditLog
from schemas.crm import (
    CRMChatRequest,
    CRMChatResponse,
    CustomerListResponse,
    ProductListResponse,
    OpportunityListResponse,
    AuditLogListResponse,
)

router = APIRouter(prefix="/crm", tags=["crm"])


@router.post("/chat", response_model=CRMChatResponse)
async def crm_chat(
    request: CRMChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Punto de entrada del agente CRM. Mantiene una conversacion persistente
    por usuario (session_id = crm-user-<id>), filtra intentos de prompt
    injection antes de invocar al agente y registra cada tool ejecutada
    en crm_audit_logs.
    """
    session_id = f"crm-user-{current_user.id}"

    injection_label = detect_prompt_injection(request.message)
    if injection_label:
        db.add(CRMAuditLog(
            user_id=current_user.id,
            session_id=session_id,
            event_type="security_block",
            tool_name=None,
            user_message=request.message,
            details={"pattern": injection_label},
            success=False,
        ))
        db.commit()
        return CRMChatResponse(
            reply=(
                "No puedo procesar esa solicitud. Por favor, reformula tu mensaje "
                "enfocandote en la gestion de clientes, oportunidades o ventas."
            ),
            blocked=True,
        )

    result = await run_crm_agent(
        message=request.message,
        user_id=str(current_user.id),
        session_id=session_id,
        user_role=current_user.role,
        db_url=get_database_url(),
        db=db,
    )

    return CRMChatResponse(
        reply=result["reply"],
        session_state=result["session_state"],
        tool_calls=result["tool_calls"],
        blocked=False,
    )


@router.get("/customers", response_model=CustomerListResponse)
def list_customers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista todos los clientes registrados (solo lectura, para demo/debug)."""
    customers = db.query(Customer).order_by(Customer.name).all()
    return CustomerListResponse(customers=customers, total=len(customers))


@router.get("/products", response_model=ProductListResponse)
def list_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista el catalogo de productos (solo lectura, para demo/debug)."""
    products = db.query(Product).order_by(Product.name).all()
    return ProductListResponse(products=products, total=len(products))


@router.get("/opportunities", response_model=OpportunityListResponse)
def list_opportunities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lista oportunidades de venta (solo lectura, para demo/debug).
    Los vendedores ('seller') solo ven las oportunidades que crearon;
    managers y admins ven todas.
    """
    query = db.query(Opportunity)
    if current_user.role == "seller":
        query = query.filter(Opportunity.created_by_id == current_user.id)
    opportunities = query.order_by(Opportunity.created_at.desc()).all()
    return OpportunityListResponse(opportunities=opportunities, total=len(opportunities))


@router.get("/audit-logs", response_model=AuditLogListResponse)
def list_audit_logs(
    limit: int = Query(default=20, ge=1, le=100),
    event_type: str | None = Query(default=None, description="Filtrar por tipo: tool_call, security_block, error"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Historial de auditoría: cada tool ejecutada, bloqueo de seguridad y error.
    Los vendedores solo ven sus propios logs; managers y admins ven todos.
    """
    query = db.query(CRMAuditLog)
    if current_user.role == "seller":
        query = query.filter(CRMAuditLog.user_id == current_user.id)
    if event_type:
        query = query.filter(CRMAuditLog.event_type == event_type)
    logs = query.order_by(CRMAuditLog.created_at.desc()).limit(limit).all()
    return AuditLogListResponse(logs=logs, total=len(logs))
