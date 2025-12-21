from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from ..core.config import settings

# Create database engine with optimized connection pool settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=20,  # Increased from default 5
    max_overflow=30,  # Allow additional connections
    pool_timeout=30,  # Connection timeout
    pool_reset_on_return='commit',  # Reset connection state
    echo=False,  # Disable SQL logging in production
    connect_args={
        "options": "-c timezone=utc -c client_encoding=utf8",
        "application_name": "phix_hrms"  # Help identify connections
    }
)

# Create SessionLocal class with optimized settings
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Prevent lazy loading issues
)

# Create Base class for models
Base = declarative_base()

# Dependency to get database session with connection management
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
