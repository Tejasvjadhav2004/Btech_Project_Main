from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# PostgreSQL engine (psycopg2-binary driver)
# Connection string is read from DATABASE_URL in .env
# Example: postgresql://postgres:password@localhost:5432/supplier_db
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,       # auto-reconnect on stale connections
    pool_size=10,             # connection pool size
    max_overflow=20,          # extra connections beyond pool_size
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
