from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.config import get_settings


Base = declarative_base()


settings = get_settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
