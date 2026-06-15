"""
Script de seed para datos demo del modulo CRM AI Agent.

Ejecutar con: python -m scripts.seed_crm
"""
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
load_dotenv()

from core.db import SessionLocal, get_engine
from core.security import hash_password
from models.user import User
from models.customer import Customer
from models.product import Product
from models.opportunity import Opportunity, OpportunityItem  # noqa: F401
from models.lead import Lead  # noqa: F401
from models.meeting import Meeting  # noqa: F401
from models.crm_audit_log import CRMAuditLog  # noqa: F401


DEMO_USERS = [
    {"email": "vendedor@nexuscrm.com", "name": "Vendedor Demo", "role": "seller"},
    {"email": "manager@nexuscrm.com", "name": "Manager Demo", "role": "manager"},
    {"email": "admin@nexuscrm.com", "name": "Admin Demo", "role": "admin"},
]

DEMO_CUSTOMERS = [
    {"name": "Acme Corp", "company": "Acme Corp", "email": "contacto@acme.com", "industry": "Manufactura"},
    {"name": "Globex Inc", "company": "Globex Inc", "email": "contacto@globex.com", "industry": "Tecnologia"},
    {"name": "Juan Perez", "company": None, "email": "juan.perez@email.com", "industry": "Independiente"},
    {"name": "Initech LLC", "company": "Initech LLC", "email": "contacto@initech.com", "industry": "Finanzas"},
    {"name": "Umbrella Corporation", "company": "Umbrella Corporation", "email": "contacto@umbrella.com", "industry": "Salud"},
    {"name": "Wayne Enterprises", "company": "Wayne Enterprises", "email": "contacto@wayne.com", "industry": "Defensa"},
]

DEMO_PRODUCTS = [
    {"name": "Licencia Enterprise", "sku": "LIC-ENT-001", "unit_price": 1200.00, "category": "Licencias"},
    {"name": "Soporte Premium", "sku": "SUP-PREM-001", "unit_price": 300.00, "category": "Soporte"},
    {"name": "Licencia Basica", "sku": "LIC-BAS-001", "unit_price": 400.00, "category": "Licencias"},
    {"name": "Soporte Basico", "sku": "SUP-BAS-001", "unit_price": 150.00, "category": "Soporte"},
    {"name": "Modulo Analytics", "sku": "ANL-MOD-001", "unit_price": 800.00, "category": "Add-ons"},
]


def seed():
    engine = get_engine()
    SessionLocal.configure(bind=engine)
    db = SessionLocal()

    try:
        for u in DEMO_USERS:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                db.add(User(
                    email=u["email"],
                    name=u["name"],
                    hashed_password=hash_password("demo1234"),
                    role=u["role"],
                ))

        for c in DEMO_CUSTOMERS:
            existing = db.query(Customer).filter(Customer.name == c["name"]).first()
            if not existing:
                db.add(Customer(**c))

        for p in DEMO_PRODUCTS:
            existing = db.query(Product).filter(Product.name == p["name"]).first()
            if not existing:
                db.add(Product(**p))

        db.flush()

        seller = db.query(User).filter(User.email == "vendedor@nexuscrm.com").first()
        manager = db.query(User).filter(User.email == "manager@nexuscrm.com").first()
        now = datetime.now(timezone.utc)

        demo_leads = [
            {"contact_name": "Maria Lopez", "company": "InnovaTech", "email": "maria@innovatech.com",
             "source": "referido", "status": "new", "created_by_id": seller.id, "created_at": now - timedelta(days=2)},
            {"contact_name": "Carlos Ruiz", "company": "DataSoft", "email": "carlos@datasoft.com",
             "source": "web", "status": "contacted", "created_by_id": seller.id, "created_at": now - timedelta(days=10)},
            {"contact_name": "Ana Torres", "company": "CloudNine", "email": "ana@cloudnine.com",
             "source": "evento", "status": "qualified", "created_by_id": manager.id, "created_at": now - timedelta(days=1)},
        ]
        for l in demo_leads:
            existing = db.query(Lead).filter(Lead.contact_name == l["contact_name"]).first()
            if not existing:
                db.add(Lead(**l))

        db.commit()
        print("Seed completado: usuarios, clientes, productos y leads demo creados.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
