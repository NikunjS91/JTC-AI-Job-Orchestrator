import json
import time
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaConsumer
from prometheus_client import Counter, Gauge, make_asgi_app
from libs.core.logger import configure_logger
from libs.core.config import BaseConfig, get_config
import threading
from queue import Queue

logger = configure_logger("orchestrator_service")

# Prometheus metrics
sse_connections = Gauge('orchestrator_sse_connections', 'Number of active SSE connections')
events_streamed = Counter('orchestrator_events_streamed_total', 'Total events streamed via SSE')
notifications_consumed = Counter('orchestrator_notifications_consumed_total', 'Total notifications consumed from Kafka')

class OrchestratorConfig(BaseConfig):
    SERVICE_NAME: str = "orchestrator"
    KAFKA_GROUP_ID: str = "orchestrator_group"

config = get_config(OrchestratorConfig)

app = FastAPI(title="Orchestrator API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Global thread-safe queue for incoming Kafka events
incoming_queue = Queue(maxsize=100)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[asyncio.Queue] = []

    async def connect(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.active_connections.append(queue)
        sse_connections.set(len(self.active_connections))
        return queue

    def disconnect(self, queue: asyncio.Queue):
        if queue in self.active_connections:
            self.active_connections.remove(queue)
            sse_connections.set(len(self.active_connections))

    async def broadcast(self, event: dict):
        for queue in self.active_connections:
            await queue.put(event)

manager = ConnectionManager()

async def event_broadcaster():
    """Background task to move events from thread-safe queue to async client queues"""
    logger.info("Starting event broadcaster task...")
    while True:
        # Non-blocking get from thread-safe queue
        try:
            # We use a small sleep to prevent busy waiting, but check frequently
            if not incoming_queue.empty():
                event = incoming_queue.get_nowait()
                await manager.broadcast(event)
                events_streamed.inc()
            else:
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in event broadcaster: {e}")
            await asyncio.sleep(1)

from libs.core.db import DatabaseClient, Application
from kafka import KafkaProducer
import datetime

# ... (imports)

# Initialize Clients
try:
    db = DatabaseClient(config)
except Exception as e:
    logger.error(f"DB Init failed: {e}")
    db = None

producer = None
try:
    producer = KafkaProducer(
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
except Exception as e:
    logger.error(f"Kafka Init failed: {e}")

# ... (ConnectionManager and event_broadcaster)

async def daily_stats_scheduler():
    """Background task to run daily stats job at 08:00 AM"""
    logger.info("Starting daily stats scheduler...")
    while True:
        now = datetime.datetime.now()
        # Run at 08:00 AM
        if now.hour == 8 and now.minute == 0:
            logger.info("Running daily stats job...")
            try:
                if db and producer:
                    session = db.Session()
                    try:
                        # Get yesterday's stats
                        yesterday = (now - datetime.timedelta(days=1)).date()
                        apps = session.query(Application).filter(Application.created_at >= yesterday).all()
                        
                        interviews = sum(1 for a in apps if a.status == 'INTERVIEW')
                        offers = sum(1 for a in apps if a.status == 'OFFER')
                        rejections = sum(1 for a in apps if a.status == 'REJECTION')
                        
                        summary_text = f"🌅 **Daily Summary** ({yesterday}):\n• {len(apps)} new events\n• {interviews} interviews\n• {offers} offers\n• {rejections} rejections"
                        
                        # Publish notification
                        event = {
                            "event_id": f"daily_stats_{int(time.time())}",
                            "event_type": "DAILY_STATS",
                            "company": "System",
                            "role": "Daily Report",
                            "summary": summary_text,
                            "classified_at": now.isoformat(),
                            "metadata": {"type": "daily_stats"}
                        }
                        producer.send('notifications', event)
                        logger.info("Published daily stats notification")
                    finally:
                        session.close()
            except Exception as e:
                logger.error(f"Daily stats job failed: {e}")
            
            # Sleep for 61 seconds to avoid double run
            await asyncio.sleep(61)
        else:
            # Check every minute
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(event_broadcaster())
    asyncio.create_task(daily_stats_scheduler())

# ... (kafka_consumer_thread)

@app.get("/stats/today")
async def stats_today():
    """Get today's statistics"""
    if not db:
        return {"error": "Database not available"}
        
    session = db.Session()
    try:
        today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        apps = session.query(Application).filter(Application.created_at >= today_start).all()
        
        interviews = sum(1 for a in apps if a.status == 'INTERVIEW')
        offers = sum(1 for a in apps if a.status == 'OFFER')
        rejections = sum(1 for a in apps if a.status == 'REJECTION')
        
        return {
            "date": today_start.strftime("%Y-%m-%d"),
            "interviews": interviews,
            "offers": offers,
            "rejections": rejections,
            "total_events": len(apps)
        }
    finally:
        session.close()

@app.get("/stats/summary")
async def stats_summary():
    """Get overall summary statistics"""
    if not db:
        return {"error": "Database not available"}
        
    session = db.Session()
    try:
        total = session.query(Application).count()
        interviews = session.query(Application).filter(Application.status == 'INTERVIEW').count()
        offers = session.query(Application).filter(Application.status == 'OFFER').count()
        rejections = session.query(Application).filter(Application.status == 'REJECTION').count()
        
        return {
            "total_interviews": interviews,
            "total_offers": offers,
            "total_rejections": rejections,
            "active_applications": total - rejections
        }
    finally:
        session.close()

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Orchestrator Service...")
    uvicorn.run(app, host="0.0.0.0", port=8005)
