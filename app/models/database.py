from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

import time
from sqlalchemy.exc import OperationalError

# Load database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost/orders_db"
)


MAX_RETRIES = 5

for i in range(MAX_RETRIES):
    try:
        engine = create_engine(DATABASE_URL)
        break
    except OperationalError:
        print(f"Database not ready, retrying ({i+1}/{MAX_RETRIES})...")
        time.sleep(5)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
