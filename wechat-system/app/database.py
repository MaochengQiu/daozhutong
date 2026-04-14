from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.config import get_settings


Base = declarative_base()


settings = get_settings()
db_url = make_url(settings.database_url)
if db_url.drivername.startswith("sqlite") and db_url.database and db_url.database != ":memory:":
    Path(db_url.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
