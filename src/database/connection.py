"""
Database engine configuration and session dependency provider.
"""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Create DB engine with connection timeouts & thread safety
connect_args = {"check_same_thread": False, "timeout": 30} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

# Enable WAL journal mode for high-concurrency SQLite operations
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db(drop_existing: bool = False) -> None:
    """Initialize database tables, option to recreate schemas."""
    # Import models to ensure they are registered with Base metadata
    from src.database.models import TransactionModel, PredictionModel, AlertModel

    if drop_existing:
        logger.info("Dropping existing database tables...")
        Base.metadata.drop_all(bind=engine)

    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")


def get_db() -> Generator:
    """FastAPI database session dependency generator."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
