from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

from src.database import get_db, engine
from libs.core.db import Base, Application
from src.consumer import run_background_consumer
from libs.core.logger import configure_logger

logger = configure_logger("dashboard_api")

# Create tables on startup (using shared Base)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CareerOps Dashboard API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start Kafka Consumer
@app.on_event("startup")
async def startup_event():
    run_background_consumer()

# Pydantic Models
class ApplicationResponse(BaseModel):
    id: str
    company: Optional[str]
    role: Optional[str]
    status: Optional[str]
    confidence: Optional[float]
    summary: Optional[str]
    research_briefing: Optional[Any]
    created_at: Optional[datetime]
    storage_path: Optional[str]

    class Config:
        orm_mode = True

class StatsResponse(BaseModel):
    total_events: int
    interviews: int
    offers: int
    rejections: int

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/applications", response_model=List[ApplicationResponse])
def get_applications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    apps = db.query(Application).order_by(Application.created_at.desc()).offset(skip).limit(limit).all()
    return apps

# Keep /events for backward compatibility if UI uses it, but map to Application
@app.get("/events", response_model=List[ApplicationResponse])
def get_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_applications(skip, limit, db)

@app.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(Application).count()
    interviews = db.query(Application).filter(Application.status == "INTERVIEW").count()
    offers = db.query(Application).filter(Application.status == "OFFER").count()
    rejections = db.query(Application).filter(Application.status == "REJECTION").count()
    
    return {
        "total_events": total,
        "interviews": interviews,
        "offers": offers,
        "rejections": rejections
    }
