from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine("sqlite:///./ecommerce.db", connect_args =  {"check_same_thread": False})

SessionLocal = sessionmaker(autocommit = False, bind = engine)

Base = declarative_base()

# DATABASE SESSION DEPENDENCY

def get_db():
    # Create new database session
    db = SessionLocal()
    try:
        # Yield session to request handler
        yield db
    finally:
        # Always close session after request (cleanup)
        db.close()