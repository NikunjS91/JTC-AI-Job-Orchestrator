import json
import threading
import time
from kafka import KafkaConsumer
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import CareerEvent
from libs.core.config import BaseConfig, get_config
from libs.core.logger import configure_logger

logger = configure_logger("dashboard_consumer")

class ConsumerConfig(BaseConfig):
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
    KAFKA_GROUP_ID: str = "dashboard_group"

config = get_config(ConsumerConfig)

def process_message(db: Session, msg_value: dict):
    try:
        event_id = msg_value.get('id') or msg_value.get('original_email_id')
        if not event_id:
            logger.warning("Message missing ID, skipping.")
            return

        # Check if exists
        existing = db.query(CareerEvent).filter(CareerEvent.event_id == event_id).first()
        
        if existing:
            # Update
            existing.event_type = msg_value.get('event_type', existing.event_type)
            existing.company = msg_value.get('company', existing.company)
            existing.confidence = msg_value.get('confidence', existing.confidence)
            existing.summary = msg_value.get('summary', existing.summary)
            existing.raw_data = msg_value
            if 'research_briefing' in msg_value:
                existing.research_briefing = msg_value['research_briefing']
            logger.info(f"Updated event {event_id}")
        else:
            # Create
            new_event = CareerEvent(
                event_id=event_id,
                event_type=msg_value.get('event_type'),
                company=msg_value.get('company'),
                confidence=msg_value.get('confidence'),
                summary=msg_value.get('summary'),
                raw_data=msg_value,
                research_briefing=msg_value.get('research_briefing')
            )
            db.add(new_event)
            logger.info(f"Created event {event_id}")
        
        db.commit()
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        db.rollback()

def start_consumer():
    logger.info("Starting Dashboard Kafka Consumer...")
    
    # Retry connection
    consumer = None
    while not consumer:
        try:
            consumer = KafkaConsumer(
                'classified_events', 'notifications',
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=config.KAFKA_GROUP_ID,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='earliest'
            )
            logger.info("Kafka Consumer connected.")
        except Exception as e:
            logger.warning(f"Waiting for Kafka... {e}")
            time.sleep(5)
            
    db = SessionLocal()
    try:
        for message in consumer:
            logger.info(f"Received message from {message.topic}")
            process_message(db, message.value)
    except Exception as e:
        logger.error(f"Consumer crashed: {e}")
    finally:
        db.close()
        consumer.close()

def run_background_consumer():
    t = threading.Thread(target=start_consumer, daemon=True)
    t.start()
