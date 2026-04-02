from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from libs.core.config import BaseConfig
from libs.core.logger import configure_logger
import datetime

logger = configure_logger("db_client")
Base = declarative_base()

class Application(Base):
    __tablename__ = 'applications'

    id = Column(String, primary_key=True)  # event_id or message_id
    company = Column(String, index=True)
    role = Column(String)
    status = Column(String)  # INTERVIEW, OFFER, REJECTION, APPLIED
    confidence = Column(Float)
    summary = Column(Text)
    research_briefing = Column(JSON)
    metadata_ = Column("metadata", JSON)  # 'metadata' is reserved in SQLAlchemy sometimes
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    storage_path = Column(String) # Link to MinIO

class DatabaseClient:
    def __init__(self, config: BaseConfig):
        self.engine = create_engine(config.DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        self._create_tables()

    def _create_tables(self):
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created/verified.")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")

    def upsert_application(self, event: dict):
        session = self.Session()
        try:
            # Map event to Application model
            app_data = {
                "id": event.get("event_id") or event.get("message_id"),
                "company": event.get("company"),
                "role": event.get("role"),
                "status": event.get("event_type"),
                "confidence": event.get("confidence"),
                "summary": event.get("summary"),
                "research_briefing": event.get("research_briefing"),
                "metadata_": event.get("metadata"),
                "storage_path": event.get("storage_path")
            }

            # Check if exists
            existing = session.query(Application).filter_by(id=app_data["id"]).first()
            if existing:
                for key, value in app_data.items():
                    setattr(existing, key, value)
                logger.info(f"Updated application {app_data['id']}")
            else:
                new_app = Application(**app_data)
                session.add(new_app)
                logger.info(f"Created application {app_data['id']}")
            
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to upsert application: {e}")
            raise e
        finally:
            session.close()
