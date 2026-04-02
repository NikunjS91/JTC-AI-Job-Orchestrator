import json
import time
from kafka import KafkaConsumer, KafkaProducer
from libs.core.logger import configure_logger
from libs.core.config import BaseConfig, get_config
from src.research_agent import ResearchAgent
from libs.core.validation import validate_classified_event
from prometheus_client import Counter, start_http_server

logger = configure_logger("researcher_service")

# Prometheus metrics
events_received = Counter('researcher_events_received_total', 'Total events received')
events_validation_errors = Counter('researcher_validation_errors_total', 'Total validation errors')
events_dlq = Counter('researcher_events_dlq_total', 'Total events sent to DLQ')
research_completed = Counter('researcher_research_completed_total', 'Total research completed')
research_failed = Counter('researcher_research_failed_total', 'Total research failures')
events_rate_limited = Counter('researcher_events_rate_limited_total', 'Total rate limit hits')

class ResearcherConfig(BaseConfig):
    SERVICE_NAME: str = "researcher"
    KAFKA_GROUP_ID: str = "researcher_group"
    # Rate limiting config (Tavily free tier: 1000/month)
    TAVILY_MONTHLY_QUOTA: int = 1000
    SAFETY_MARGIN: float = 0.8  # Use only 80% of quota

config = get_config(ResearcherConfig)

# Calculate delay to stay under quota (1000/month = ~33/day)
SECONDS_PER_DAY = 86400
DAILY_QUOTA = int((config.TAVILY_MONTHLY_QUOTA / 30) * config.SAFETY_MARGIN)
RATE_LIMIT_DELAY = int(SECONDS_PER_DAY / DAILY_QUOTA) if DAILY_QUOTA > 0 else 3600
logger.info(f"Rate limit: Processing 1 research every {RATE_LIMIT_DELAY} seconds (~{DAILY_QUOTA}/day)")

from libs.core.db import DatabaseClient

# ... (imports)

def main():
    logger.info("Starting Researcher Service...")
    
    # Start Prometheus metrics server
    start_http_server(8003)
    logger.info("Prometheus metrics available at :8003/metrics")
    
    agent = ResearchAgent()
    db = DatabaseClient(config)
    
    # Wait for Kafka
    consumer = None
    while not consumer:
        try:
            consumer = KafkaConsumer(
                'classified_events',
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=config.KAFKA_GROUP_ID,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='earliest'
            )
            logger.info("Kafka Consumer connected.")
        except Exception as e:
            logger.warning(f"Waiting for Kafka... {e}")
            time.sleep(5)

    producer = KafkaProducer(
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    logger.info("Listening for classified events...")
    
    for message in consumer:
        event = message.value
        events_received.inc()
        logger.info(f"Received event: {event.get('event_type')} for {event.get('company')}")

        # Basic validation of classified event
        ok, err = validate_classified_event({
            "event_id": event.get("event_id", event.get("original_email_id", "")),
            "message_id": event.get("original_email_id", ""),
            "event_type": event.get("event_type", "UNKNOWN"),
            "company": event.get("company"),
            "role": event.get("role"),
            "confidence": float(event.get("confidence", 0.0)),
            "classified_at": event.get("classified_at"),
            "metadata": event.get("metadata"),
            "research_briefing": event.get("research_briefing"),
        })
        if not ok:
            events_validation_errors.inc()
            logger.error(f"Invalid classified event in researcher: {err}")
            producer.send('dlq.classified_events', {"error": "invalid_classified_event", "details": err, "original": event, "source": "researcher"})
            events_dlq.inc()
            continue
        
        if event.get('company'):
            try:
                briefing = agent.research_company(event['company'])
                event['research_briefing'] = briefing
                
                # Persist to Postgres
                try:
                    db.upsert_application(event)
                    logger.info("Persisted application to Postgres.")
                except Exception as e:
                    logger.error(f"Failed to persist to DB: {e}")
                    # Don't fail the whole flow, just log
                
                # Produce to notifications topic
                producer.send('notifications', event)
                research_completed.inc()
                logger.info("Research complete. Published to notifications.")
            
            except Exception as e:
                error_msg = str(e)
                # Handle rate limit errors
                if "429" in error_msg or "rate" in error_msg.lower() or "quota" in error_msg.lower():
                    events_rate_limited.inc()
                    logger.warning(f"Rate limit hit: {error_msg}")
                    logger.warning("Sleeping 60s before retrying...")
                    time.sleep(60)
                    continue  # Kafka will retry
                else:
                    research_failed.inc()
                    logger.error(f"Research failed: {e}")
                    # Send notification anyway with "Research failed" message
                    event['research_briefing'] = "Research failed..."
                    producer.send('notifications', event)
        else:
            logger.warning("No company name found in event.")
        
        # Throttle to stay under quota
        logger.debug(f"Sleeping {RATE_LIMIT_DELAY}s (rate limiting)...")
        time.sleep(RATE_LIMIT_DELAY)

if __name__ == "__main__":
    main()
