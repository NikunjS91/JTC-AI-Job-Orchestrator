from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from libs.core.config import BaseConfig, get_config

class DBConfig(BaseConfig):
    # Default to the docker-compose service name 'postgres'
    DATABASE_URL: str = "postgresql://airflow:airflow_password@postgres:5432/airflow"

config = get_config(DBConfig)

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
