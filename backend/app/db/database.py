"""
Database connection and session management for DataContractIQ
Provides SQLAlchemy engine, session factory, and connection utilities
"""
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine, Inspector
from sqlalchemy.pool import NullPool
from typing import Generator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection pooling
# Using NullPool for introspection tasks to avoid connection issues
engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=settings.debug,  # Log SQL queries in debug mode
    future=True  # Use SQLAlchemy 2.0 style
)

# Session factory for creating database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI endpoints to get database session.
    Automatically handles session lifecycle (create, use, close).
    
    Usage in FastAPI:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db session here
            pass
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_inspector() -> Inspector:
    """
    Get SQLAlchemy Inspector for schema introspection.
    Inspector provides access to database metadata without ORM models.
    
    Returns:
        Inspector: SQLAlchemy Inspector instance bound to the engine
    """
    return inspect(engine)


def test_connection() -> bool:
    """
    Test database connection and return success status.
    Useful for health checks and startup validation.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def get_database_version() -> str:
    """
    Get PostgreSQL database version string.
    
    Returns:
        str: Database version (e.g., "PostgreSQL 14.5")
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            return version.split(",")[0] if version else "Unknown"
    except Exception as e:
        logger.error(f"Failed to get database version: {e}")
        return "Unknown"


def get_table_names(schema: str = "public") -> list[str]:
    """
    Get list of all table names in the specified schema.
    
    Args:
        schema: Database schema name (default: "public")
    
    Returns:
        list[str]: List of table names
    """
    inspector = get_inspector()
    return inspector.get_table_names(schema=schema)


def table_exists(table_name: str, schema: str = "public") -> bool:
    """
    Check if a table exists in the database.
    
    Args:
        table_name: Name of the table to check
        schema: Database schema name (default: "public")
    
    Returns:
        bool: True if table exists, False otherwise
    """
    inspector = get_inspector()
    return table_name in inspector.get_table_names(schema=schema)


# Event listener to log connection pool events in debug mode
@event.listens_for(Engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log database connections in debug mode"""
    if settings.debug:
        logger.debug("Database connection established")


@event.listens_for(Engine, "close")
def receive_close(dbapi_conn, connection_record):
    """Log database disconnections in debug mode"""
    if settings.debug:
        logger.debug("Database connection closed")


# Made with Bob