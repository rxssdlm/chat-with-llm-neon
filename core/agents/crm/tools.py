"""
Tools del Agente CRM.

Convencion: ninguna tool lanza excepciones hacia el agente. Siempre devuelven
un dict con "success": bool y, segun el caso, los datos o un "error": str.
El agente esta instruido para traducir "success": False en una explicacion
clara para el usuario (ver agent.py -> CRM_INSTRUCTIONS).

Cada tool recibe `run_context: RunContext` (inyectado automaticamente por Agno),
desde donde se accede a `run_context.session_state` (dict mutable y persistido
entre turnos via PostgresDb).
"""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from agno.tools import tool
from agno.run.base import RunContext

from core.db import SessionLocal, get_engine
from models.user import User  # noqa: F401 - necesario para resolver relaciones de CRMAuditLog/Opportunity/Lead/Meeting
from models.customer import Customer
from models.product import Product
from models.opportunity import Opportunity, OpportunityItem
from models.lead import Lead
from models.meeting import Meeting
from core.agents.crm.permissions import (
    can_approve_discount,
    requires_confirmation_for_discount,
    requires_confirmation_for_amount,
    DISCOUNT_APPROVAL_THRESHOLD_PCT,
    SALE_AMOUNT_CONFIRMATION_THRESHOLD,
)


@contextmanager
def _db_session():
    engine = get_engine()
    SessionLocal.configure(bind=engine)
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _resolve_customer(db, name: str) -> Customer | None:
    return db.query(Customer).filter(
        or_(Customer.name.ilike(f"%{name}%"), Customer.company.ilike(f"%{name}%"))
    ).first()


def _coerce_int(value, field_name: str) -> int:
    """Convierte a int valores que Groq a veces envia como string (ej. '20')."""
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{field_name}' debe ser un numero entero, recibi: {value!r}.")


def _coerce_float(value, field_name: str) -> float:
    """Convierte a float valores que Groq a veces envia como string (ej. '40')."""
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{field_name}' debe ser un numero, recibi: {value!r}.")


def _resolve_product(db, product_name: str) -> Product | None:
    products = db.query(Product).filter(Product.name.ilike(f"%{product_name}%")).all()
    if not products:
        return None
    if len(products) == 1:
        return products[0]
    # Si hay varias coincidencias (ej. "licencias" -> Enterprise y Basica),
    # preferir la variante "Enterprise" como heuristica por defecto.
    for p in products:
        if "enterprise" in p.name.lower():
            return p
    return products[0]


@tool
def search_customer(query: str, run_context: RunContext) -> dict:
    """Busca un cliente por nombre o empresa (busqueda parcial, sin distinguir mayusculas)."""
    session_state = run_context.session_state
    try:
        with _db_session() as db:
            customers = db.query(Customer).filter(
                or_(Customer.name.ilike(f"%{query}%"), Customer.company.ilike(f"%{query}%"))
            ).all()
            if not customers:
                return {"success": False, "error": f"No se encontro ningun cliente que coincida con '{query}'."}

            results = [
                {"id": c.id, "name": c.name, "company": c.company, "email": c.email, "industry": c.industry}
                for c in customers
            ]

            best = customers[0]
            session_state["customer"] = {"id": best.id, "name": best.name, "company": best.company}
            session_state["last_tool_used"] = "search_customer"

            return {"success": True, "customers": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_products(run_context: RunContext, query: str | None = None) -> dict:
    """Devuelve el catalogo de productos disponibles, opcionalmente filtrado por nombre."""
    session_state = run_context.session_state
    try:
        with _db_session() as db:
            q = db.query(Product)
            if query:
                q = q.filter(Product.name.ilike(f"%{query}%"))
            products = q.order_by(Product.name).all()
            results = [
                {"id": p.id, "name": p.name, "sku": p.sku, "unit_price": float(p.unit_price), "category": p.category}
                for p in products
            ]
            session_state["last_tool_used"] = "get_products"
            return {"success": True, "products": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def create_lead(
    contact_name: str,
    run_context: RunContext,
    company: str | None = None,
    email: str | None = None,
    source: str | None = None,
) -> dict:
    """Crea un nuevo lead (prospecto) con un contacto, empresa, correo y fuente opcionales."""
    session_state = run_context.session_state
    try:
        with _db_session() as db:
            user_id = session_state.get("user_id")
            lead = Lead(
                contact_name=contact_name,
                company=company,
                email=email,
                source=source,
                status="new",
                created_by_id=int(user_id) if user_id else None,
            )
            db.add(lead)
            db.flush()
            session_state["last_tool_used"] = "create_lead"
            return {"success": True, "lead_id": lead.id, "contact_name": lead.contact_name}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def create_customer(
    name: str,
    run_context: RunContext,
    company: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    industry: str | None = None,
) -> dict:
    """Registra un nuevo cliente (no un lead/prospecto). Antes de crear, verifica con search_customer que no exista ya."""
    session_state = run_context.session_state
    try:
        with _db_session() as db:
            existing = _resolve_customer(db, name)
            if existing:
                return {
                    "success": False,
                    "error": f"Ya existe un cliente similar: '{existing.name}'. Usa search_customer para verificarlo antes de crear uno nuevo.",
                }

            customer = Customer(name=name, company=company, email=email, phone=phone, industry=industry)
            db.add(customer)
            db.flush()

            session_state["customer"] = {"id": customer.id, "name": customer.name, "company": customer.company}
            session_state["last_tool_used"] = "create_customer"

            return {"success": True, "customer_id": customer.id, "name": customer.name, "company": customer.company}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def create_opportunity(customer_name: str, product_name: str, quantity: int | str, run_context: RunContext) -> dict:
    """
    Crea una oportunidad para un cliente con un producto y cantidad inicial. Para agregar
    productos a una oportunidad existente usa update_opportunity. Si el monto supera el
    umbral de confirmacion, devuelve 'requires_confirmation': true sin crear nada; espera
    confirmacion antes de reintentar con los mismos parametros.
    """
    session_state = run_context.session_state
    try:
        with _db_session() as db:
            pending = session_state.get("pending_action")
            is_confirmation = bool(
                pending
                and pending.get("type") == "create_opportunity"
                # Una pending_action creada en ESTE mismo run (turno) nunca se
                # autoconfirma, sin importar cuantas veces el LLM reintente la
                # llamada: la confirmacion solo es valida si viene de un turno
                # anterior (run_id distinto), es decir, de un mensaje nuevo del
                # usuario.
                and pending.get("created_in_run_id") != run_context.run_id
            )

            if is_confirmation:
                # Una vez que hay una accion pendiente, esta es la fuente de verdad:
                # usamos los IDs ya resueltos en pending_action en lugar de volver a
                # resolver customer_name/product_name (el LLM puede repetir un nombre
                # de cliente/producto distinto al confirmar, p.ej. el "cliente activo"
                # de la conversacion en vez del de la accion pendiente).
                customer = db.query(Customer).filter(Customer.id == pending["customer_id"]).first()
                product = db.query(Product).filter(Product.id == pending["product_id"]).first()
                quantity = pending["quantity"]
                total_amount = pending["total_amount"]
                if not customer or not product:
                    session_state["pending_action"] = None
                    return {
                        "success": False,
                        "error": "La accion pendiente ya no es valida (cliente o producto no encontrado). Por favor solicita la oportunidad de nuevo.",
                    }
            else:
                customer = _resolve_customer(db, customer_name)
                if not customer:
                    return {
                        "success": False,
                        "error": f"No se encontro ningun cliente que coincida con '{customer_name}'. Verifica el nombre con search_customer.",
                    }

                product = _resolve_product(db, product_name)
                if not product:
                    return {"success": False, "error": f"No se encontro ningun producto que coincida con '{product_name}'."}

                quantity = _coerce_int(quantity, "quantity")
                total_amount = float(product.unit_price) * quantity

            if requires_confirmation_for_amount(total_amount) and not is_confirmation:
                session_state["pending_action"] = {
                    "type": "create_opportunity",
                    "customer_id": customer.id,
                    "product_id": product.id,
                    "quantity": quantity,
                    "total_amount": total_amount,
                    "created_in_run_id": run_context.run_id,
                }
                return {
                    "success": True,
                    "requires_confirmation": True,
                    "message": (
                        f"La oportunidad para {customer.name} por {quantity} x {product.name} "
                        f"suma ${total_amount:,.2f}, lo cual supera el umbral de "
                        f"${SALE_AMOUNT_CONFIRMATION_THRESHOLD:,.2f} que requiere confirmacion. "
                        "¿Confirmas que deseas crear esta oportunidad?"
                    ),
                }

            if is_confirmation:
                session_state["pending_action"] = None

            user_id = session_state.get("user_id")
            opportunity = Opportunity(
                customer_id=customer.id,
                created_by_id=int(user_id) if user_id else None,
                name=f"Oportunidad {customer.name}",
                stage="prospecting",
                total_amount=total_amount,
            )
            db.add(opportunity)
            db.flush()

            db.add(OpportunityItem(
                opportunity_id=opportunity.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.unit_price,
            ))
            items_out = [{"product_name": product.name, "quantity": quantity, "unit_price": float(product.unit_price)}]

            session_state["customer"] = {"id": customer.id, "name": customer.name, "company": customer.company}
            session_state["opportunity"] = {
                "id": opportunity.id,
                "name": opportunity.name,
                "stage": opportunity.stage,
                "total_amount": total_amount,
                "discount_pct": 0,
                "items": items_out,
            }
            session_state["current_stage"] = "prospecting"
            session_state["last_tool_used"] = "create_opportunity"

            return {
                "success": True,
                "opportunity_id": opportunity.id,
                "customer": customer.name,
                "total_amount": total_amount,
                "items": items_out,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def update_opportunity(
    run_context: RunContext,
    opportunity_id: int | str | None = None,
    add_product_name: str | None = None,
    add_quantity: int | str | None = None,
    discount_pct: float | str | None = None,
    stage: str | None = None,
) -> dict:
    """
    Actualiza una oportunidad: agrega un producto (add_product_name/add_quantity), aplica
    un descuento o cambia su etapa. Si 'opportunity_id' se omite, usa la oportunidad activa.
    Descuentos > 20% requieren confirmacion y rol manager/admin.
    """
    session_state = run_context.session_state
    try:
        if opportunity_id is not None:
            try:
                opportunity_id = int(opportunity_id)
            except (TypeError, ValueError):
                pass
        opp_id = opportunity_id or (session_state.get("opportunity") or {}).get("id")
        if not opp_id:
            return {
                "success": False,
                "error": "No hay ninguna oportunidad activa en esta conversacion. Crea una primero o especifica el cliente.",
            }

        with _db_session() as db:
            opportunity = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
            if not opportunity:
                return {"success": False, "error": f"No se encontro la oportunidad #{opp_id}."}

            if add_product_name:
                product = _resolve_product(db, add_product_name)
                if not product:
                    return {"success": False, "error": f"No se encontro ningun producto que coincida con '{add_product_name}'."}
                db.add(OpportunityItem(
                    opportunity_id=opportunity.id,
                    product_id=product.id,
                    quantity=_coerce_int(add_quantity, "add_quantity") if add_quantity is not None else 1,
                    unit_price=product.unit_price,
                ))
                db.flush()

            if discount_pct is not None:
                discount_pct = _coerce_float(discount_pct, "discount_pct")
                pending = session_state.get("pending_action")
                is_confirmation = bool(
                    pending
                    and pending.get("type") == "apply_discount"
                    and pending.get("opportunity_id") == opportunity.id
                    # Igual que en create_opportunity: una pending_action creada en
                    # este mismo turno nunca se autoconfirma.
                    and pending.get("created_in_run_id") != run_context.run_id
                )

                if is_confirmation:
                    # El descuento propuesto originalmente es la fuente de verdad,
                    # no el que el LLM repita al confirmar.
                    discount_pct = pending["discount_pct"]

                if requires_confirmation_for_discount(discount_pct) and not is_confirmation:
                    session_state["pending_action"] = {
                        "type": "apply_discount",
                        "opportunity_id": opportunity.id,
                        "discount_pct": discount_pct,
                        "created_in_run_id": run_context.run_id,
                    }
                    return {
                        "success": True,
                        "requires_confirmation": True,
                        "message": (
                            f"Un descuento de {discount_pct}% supera el {DISCOUNT_APPROVAL_THRESHOLD_PCT}% "
                            "y requiere autorizacion de un manager o admin. ¿Confirmas que deseas aplicarlo?"
                        ),
                    }

                if is_confirmation:
                    role = session_state.get("user_role", "seller")
                    if not can_approve_discount(role, discount_pct):
                        session_state["pending_action"] = None
                        return {
                            "success": False,
                            "error": (
                                f"Tu rol actual ('{role}') no tiene permisos para aprobar descuentos mayores "
                                f"al {DISCOUNT_APPROVAL_THRESHOLD_PCT}%. Se requiere rol manager o admin."
                            ),
                        }
                    session_state["pending_action"] = None

                opportunity.discount_pct = discount_pct

            if stage:
                opportunity.stage = stage

            # Recalcular el total a partir de los items actuales en BD
            opp_items = db.query(OpportunityItem).filter(OpportunityItem.opportunity_id == opportunity.id).all()
            items_total = sum(float(i.unit_price) * i.quantity for i in opp_items)
            discount = float(opportunity.discount_pct or 0)
            opportunity.total_amount = items_total * (1 - discount / 100)

            items_out = []
            for i in opp_items:
                product = db.query(Product).filter(Product.id == i.product_id).first()
                items_out.append({"product_name": product.name, "quantity": i.quantity, "unit_price": float(i.unit_price)})

            session_state["opportunity"] = {
                "id": opportunity.id,
                "name": opportunity.name,
                "stage": opportunity.stage,
                "total_amount": float(opportunity.total_amount),
                "discount_pct": discount,
                "items": items_out,
            }
            session_state["last_tool_used"] = "update_opportunity"

            return {
                "success": True,
                "opportunity_id": opportunity.id,
                "stage": opportunity.stage,
                "total_amount": float(opportunity.total_amount),
                "discount_pct": discount,
                "items": items_out,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def schedule_meeting(
    title: str,
    scheduled_at: str,
    run_context: RunContext,
    customer_name: str | None = None,
    opportunity_id: int | None = None,
    participants: str | None = None,
) -> dict:
    """
    Agenda una reunion. Requiere 'title', 'scheduled_at' (ISO 8601, ej. '2026-06-15T10:00:00'),
    un cliente (explicito o el activo de la conversacion) y 'participants' (nombres separados
    por coma, ej. 'Juan Perez, Roxana'). Si falta alguno de estos datos, NO llames esta
    herramienta todavia: pidelos primero.
    """
    session_state = run_context.session_state
    try:
        try:
            when = datetime.fromisoformat(scheduled_at)
        except ValueError:
            return {
                "success": False,
                "error": f"No pude interpretar la fecha/hora '{scheduled_at}'. Usa formato ISO 8601, ej: '2026-06-15T10:00:00'.",
            }

        with _db_session() as db:
            customer = None
            if customer_name:
                customer = _resolve_customer(db, customer_name)
            elif session_state.get("customer"):
                customer = db.query(Customer).filter(Customer.id == session_state["customer"]["id"]).first()

            if not customer:
                return {"success": False, "error": "No se especifico un cliente valido para la reunion."}

            opp_id = opportunity_id or (session_state.get("opportunity") or {}).get("id")
            user_id = session_state.get("user_id")

            meeting = Meeting(
                customer_id=customer.id,
                opportunity_id=opp_id,
                created_by_id=int(user_id) if user_id else None,
                title=title,
                scheduled_at=when,
                status="scheduled",
                notes=f"Participantes: {participants}" if participants else None,
            )
            db.add(meeting)
            db.flush()

            session_state["meeting_scheduled"] = True
            session_state["last_tool_used"] = "schedule_meeting"

            return {
                "success": True,
                "meeting_id": meeting.id,
                "customer": customer.name,
                "scheduled_at": when.isoformat(),
                "participants": participants,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_sales_metrics(run_context: RunContext) -> dict:
    """
    Metricas del pipeline: oportunidades por etapa, valor total, leads por estado y
    reuniones agendadas. 'seller' solo ve sus propias oportunidades; manager/admin ven todas.
    """
    session_state = run_context.session_state
    try:
        with _db_session() as db:
            query = db.query(Opportunity)
            role = session_state.get("user_role", "seller")
            user_id = session_state.get("user_id")
            if role == "seller" and user_id:
                query = query.filter(Opportunity.created_by_id == int(user_id))

            opportunities = query.all()
            by_stage: dict[str, int] = {}
            pipeline_value = 0.0
            for o in opportunities:
                by_stage[o.stage] = by_stage.get(o.stage, 0) + 1
                if o.stage != "closed_lost":
                    pipeline_value += float(o.total_amount)

            leads_by_status: dict[str, int] = {}
            for lead in db.query(Lead).all():
                leads_by_status[lead.status] = leads_by_status.get(lead.status, 0) + 1

            meetings_count = db.query(Meeting).count()

            session_state["last_tool_used"] = "get_sales_metrics"

            return {
                "success": True,
                "metrics": {
                    "opportunities_by_stage": by_stage,
                    "pipeline_value": pipeline_value,
                    "leads_by_status": leads_by_status,
                    "meetings_scheduled": meetings_count,
                },
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def send_email(to: str, subject: str, body: str, run_context: RunContext) -> dict:
    """Envia un correo electronico (simulado). Util para confirmar reuniones o enviar propuestas."""
    session_state = run_context.session_state
    try:
        if "fail" in to.lower():
            return {
                "success": False,
                "error": f"No se pudo enviar el correo a '{to}': direccion de correo invalida o servidor de correo no disponible.",
            }
        session_state["last_tool_used"] = "send_email"
        return {"success": True, "message": f"Correo enviado a {to} con asunto '{subject}'."}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_customer_overview(customer_name: str, run_context: RunContext) -> dict:
    """
    Vista 360 de un cliente: contacto, oportunidades (etapa, monto, descuento), leads y
    reuniones. Usala para "como va Globex" / "cual es el estatus de Acme".
    """
    session_state = run_context.session_state
    try:
        with _db_session() as db:
            customer = _resolve_customer(db, customer_name)
            if not customer:
                return {"success": False, "error": f"No se encontro ningun cliente que coincida con '{customer_name}'."}

            role = session_state.get("user_role", "seller")
            user_id = session_state.get("user_id")

            opp_query = db.query(Opportunity).filter(Opportunity.customer_id == customer.id)
            if role == "seller" and user_id:
                opp_query = opp_query.filter(Opportunity.created_by_id == int(user_id))
            opportunities = [
                {
                    "id": o.id,
                    "stage": o.stage,
                    "total_amount": float(o.total_amount),
                    "discount_pct": float(o.discount_pct or 0),
                }
                for o in opp_query.all()
            ]

            lead_query = db.query(Lead).filter(Lead.customer_id == customer.id)
            if role == "seller" and user_id:
                lead_query = lead_query.filter(Lead.created_by_id == int(user_id))
            leads = [
                {"id": l.id, "contact_name": l.contact_name, "status": l.status}
                for l in lead_query.all()
            ]

            meeting_query = db.query(Meeting).filter(Meeting.customer_id == customer.id)
            if role == "seller" and user_id:
                meeting_query = meeting_query.filter(Meeting.created_by_id == int(user_id))
            meetings = [
                {"id": m.id, "title": m.title, "scheduled_at": m.scheduled_at.isoformat(), "status": m.status}
                for m in meeting_query.all()
            ]

            session_state["customer"] = {"id": customer.id, "name": customer.name, "company": customer.company}
            session_state["last_tool_used"] = "get_customer_overview"

            return {
                "success": True,
                "customer": {
                    "id": customer.id,
                    "name": customer.name,
                    "company": customer.company,
                    "email": customer.email,
                    "industry": customer.industry,
                },
                "opportunities": opportunities,
                "leads": leads,
                "meetings": meetings,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_my_leads(run_context: RunContext, since: str | None = None) -> dict:
    """
    Leads creados por el usuario actual desde 'since' (ISO 8601, ej. '2026-06-01'),
    agrupados por estado. Si se omite, usa los ultimos 7 dias ("mis leads de esta semana").
    """
    session_state = run_context.session_state
    try:
        if since:
            try:
                since_dt = datetime.fromisoformat(since)
            except ValueError:
                return {
                    "success": False,
                    "error": f"No pude interpretar la fecha '{since}'. Usa formato ISO 8601, ej: '2026-06-01'.",
                }
        else:
            since_dt = datetime.now(timezone.utc) - timedelta(days=7)

        if since_dt.tzinfo is None:
            since_dt = since_dt.replace(tzinfo=timezone.utc)

        user_id = session_state.get("user_id")

        with _db_session() as db:
            query = db.query(Lead).filter(Lead.created_at >= since_dt)
            if user_id:
                query = query.filter(Lead.created_by_id == int(user_id))
            leads = query.order_by(Lead.created_at.desc()).all()

            results = [
                {
                    "id": l.id,
                    "contact_name": l.contact_name,
                    "company": l.company,
                    "status": l.status,
                    "source": l.source,
                    "created_at": l.created_at.isoformat(),
                }
                for l in leads
            ]
            by_status: dict[str, int] = {}
            for l in leads:
                by_status[l.status] = by_status.get(l.status, 0) + 1

            session_state["last_tool_used"] = "get_my_leads"

            return {
                "success": True,
                "since": since_dt.isoformat(),
                "total": len(results),
                "by_status": by_status,
                "leads": results,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
