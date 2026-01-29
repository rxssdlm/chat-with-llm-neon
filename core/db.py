import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

class Base(DeclarativeBase):
    pass

def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no está configurado. Revisa chat-with-llm/.env")
    return url


def get_engine():
    return create_engine(get_database_url(), pool_pre_ping=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def get_db():
    engine = get_engine()
    SessionLocal.configure(bind=engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()