from logging.config import fileConfig
import os

from dotenv import load_dotenv
load_dotenv()  # ✅ cargar .env ANTES de importar core.db

from alembic import context
from sqlalchemy import engine_from_config, pool
from models.user import User 

from core.db import Base
from models.customer import Customer
from models.product import Product
from models.opportunity import Opportunity, OpportunityItem
from models.lead import Lead
from models.meeting import Meeting
from models.crm_audit_log import CRMAuditLog

target_metadata = Base.metadata


# Alembic Config
config = context.config

# Cargar variables desde .env
load_dotenv()

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata para autogenerate
target_metadata = Base.metadata


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no está configurado. Revisa chat-with-llm/.env")
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = _get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
