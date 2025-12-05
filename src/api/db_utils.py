from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from src.core.config import get_settings
from src.core.logging import setup_logger

logger = setup_logger("database")

# Get database configuration from centralized settings (ARCH-004)
settings = get_settings()
DATABASE_URL = settings.database.url

# Configure engine based on database type
if DATABASE_URL.startswith("sqlite"):
    # SQLite with thread-safe StaticPool for concurrent access
    # StaticPool ensures single connection with serialized access
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    logger.info("Using SQLite database with StaticPool for thread safety")
else:
    # PostgreSQL/MySQL - proper connection pooling for production
    pool_size = settings.database.pool_size
    max_overflow = settings.database.max_overflow
    engine = create_engine(
        DATABASE_URL,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,  # Verify connections before use
    )
    logger.info(f"Using external database with pool_size={pool_size}, max_overflow={max_overflow}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Get database session with proper lifecycle management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> dict:
    """Check database connectivity for health endpoint (CQ-102: ensure session cleanup)."""
    db = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "type": "sqlite" if DATABASE_URL.startswith("sqlite") else "external"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
    finally:
        if db is not None:
            db.close()
