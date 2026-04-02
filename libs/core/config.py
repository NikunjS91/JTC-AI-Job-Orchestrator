from pydantic_settings import BaseSettings
from functools import lru_cache

class BaseConfig(BaseSettings):
    """
    Base configuration with common settings.
    """
    ENV: str = "development"
    SERVICE_NAME: str
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    LOG_LEVEL: str = "INFO"
    
    # MinIO Settings
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minio_admin"
    MINIO_SECRET_KEY: str = "minio_password"
    MINIO_SECURE: bool = False
    
    # Database Settings
    DATABASE_URL: str = "postgresql://airflow:airflow_password@postgres:5432/airflow"

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_config(config_cls):
    return config_cls()
