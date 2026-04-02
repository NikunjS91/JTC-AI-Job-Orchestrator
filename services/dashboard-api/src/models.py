from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from src.database import Base

class CareerEvent(Base):
    __tablename__ = "career_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True) # Original email ID or unique event ID
    event_type = Column(String, index=True) # INTERVIEW, OFFER, REJECTION, OTHER
    company = Column(String, index=True)
    confidence = Column(Float)
    summary = Column(Text)
    raw_data = Column(JSON) # Store full event payload
    research_briefing = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
