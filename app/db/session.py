# app/db/session.py
# This file sets up the database connection and session factory.
# Every database operation in this app goes through a session created here.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db.models import Base

# Create the database engine using the connection URL from .env
# The engine is the core connection to PostgreSQL
engine = create_engine(
    settings.database_url,
    echo=False  # Set to True if you want to see SQL queries in terminal (for debugging)
)


# SessionLocal is a factory that creates new database sessions
# Each request gets its own session — opened at start, closed at end
SessionLocal = sessionmaker(
    autocommit=False,  # We control when to commit (save) changes
    autoflush=False,   # We control when to flush changes to DB
    bind=engine
)


def create_tables():
    """
    Create all tables in the database if they don't exist yet.
    This reads the table definitions from models.py and creates them in PostgreSQL.
    Called once when the app starts.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Provides a database session for each API request.
    Automatically closes the session when the request is done.
    Used as a FastAPI dependency in route files.

    Usage in a route:
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()