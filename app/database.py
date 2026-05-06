from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Connect to the SQLite database file; check_same_thread=False allows FastAPI's async threads to share the connection
engine = create_engine("sqlite:///./ecommerce.db", connect_args={"check_same_thread": False})

# Factory that creates new database sessions; autocommit=False means we control when changes are saved
SessionLocal = sessionmaker(autocommit=False, bind=engine)

# Base class that all SQLAlchemy models inherit from so they get tracked and mapped to tables
Base = declarative_base()

def get_db():
    # Open a new session for the incoming request
    db = SessionLocal()
    try:
        # Hand the session to the route handler via FastAPI's dependency injection
        yield db
    finally:
        # Always close the session after the request finishes to free the connection
        db.close()
