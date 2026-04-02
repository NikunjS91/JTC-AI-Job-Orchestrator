print("DEBUG: Script started (line 1)")
import json
import time
import datetime
from kafka import KafkaConsumer, KafkaProducer
from libs.core.logger import configure_logger
from libs.core.config import BaseConfig, get_config
from libs.core.validation import validate_raw_email, validate_classified_event
from libs.core.llm_client import LLMClient
from prometheus_client import Counter, start_http_server

logger = configure_logger("classifier_service")

# Prometheus metrics
events_received = Counter('classifier_events_received_total', 'Total events received')
events_validation_errors = Counter('classifier_validation_errors_total', 'Total validation errors')
events_dlq = Counter('classifier_events_dlq_total', 'Total events sent to DLQ')
events_classified = Counter('classifier_events_classified_total', 'Total events classified', ['event_type'])

class ClassifierConfig(BaseConfig):
    SERVICE_NAME: str = "classifier"
    KAFKA_GROUP_ID: str = "classifier_group_llm"

config = get_config(ClassifierConfig)

def main():
    logger.info("Starting Classifier Service (LLM Client)...")
    
    # Start Prometheus metrics server
    start_http_server(8002)
    logger.info("Prometheus metrics available at :8002/metrics")
    
    # Initialize LLM Client
    logger.info("Initializing LLM Client...")
    try:
        llm = LLMClient()
        logger.info("LLM Client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize LLM Client: {e}")
        # We might want to exit if LLM fails, or retry. For now, exit to let Docker restart.
        return

    # Wait for Kafka
    consumer = None
    while not consumer:
        try:
            consumer = KafkaConsumer(
                'raw_inbox_stream',
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=config.KAFKA_GROUP_ID,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest'
            )
            logger.info("Kafka Consumer connected.")
        except Exception as e:
            logger.warning(f"Waiting for Kafka... {e}")
            time.sleep(5)

    producer = KafkaProducer(
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    logger.info("Listening for messages on 'raw_inbox_stream'...")
    
    for message in consumer:
        email_data = message.value
        events_received.inc()
        msg_id = email_data.get('message_id', email_data.get('id', 'unknown'))
        logger.info(f"Received email: {msg_id}")

        # Validate raw email shape
        ok, err = validate_raw_email(email_data)
        if not ok:
            events_validation_errors.inc()
            logger.error(f"raw_inbox_stream payload invalid: {err}")
            continue

        snippet = email_data.get('snippet', '')
        if not snippet:
            logger.warning("Empty snippet, skipping.")
            continue
        
        try:
            # LLM Classification
            start_time = time.time()
            llm_result_json = llm.classify_email(snippet)
            duration = time.time() - start_time
            
            if not llm_result_json:
                logger.error("LLM returned None, skipping.")
                continue

            # Parse JSON response
            try:
                # LLMClient returns a string that SHOULD be JSON.
                # Sometimes it might have markdown backticks, clean them.
                cleaned_json = llm_result_json.replace("```json", "").replace("```", "").strip()
                result = json.loads(cleaned_json)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON: {e} | Raw: {llm_result_json}")
                continue

            top_label = result.get('event_type', 'OTHER')
            top_score = result.get('confidence', 0.0)
            summary = result.get('summary', '')
            company = result.get('company', 'Unknown')
            
            logger.info(f"Classified in {duration:.2f}s: {top_label} ({top_score:.2f}) - {company}")
            
            event_type = top_label.upper() # Ensure uppercase
            
            if event_type == "OTHER":
                events_classified.labels(event_type='OTHER').inc()
                logger.info("Ignored event (OTHER)")
                continue

            # Construct Classified Event
            classified_event = {
                "event_id": f"cls_{msg_id}",
                "message_id": msg_id,
                "event_type": event_type,
                "company": company,
                "role": "General", # Could extract if we ask LLM
                "confidence": top_score,
                "classified_at": datetime.datetime.utcnow().isoformat(),
                "metadata": {
                    "model": "llm-auto",
                    "snippet": snippet[:200]
                },
                "research_briefing": summary
            }
            
            if event_type in ['INTERVIEW', 'OFFER', 'REJECTION']:
                producer.send('classified_events', classified_event)
                events_classified.labels(event_type=event_type).inc()
                logger.info(f"Published event: {event_type}")
            else:
                 # Should be covered by OTHER above, but just in case
                events_classified.labels(event_type='OTHER').inc()
                logger.info(f"Ignored event ({event_type})")

        except Exception as e:
            logger.error(f"Classification failed: {e}")
            # No rate limit sleep needed!

if __name__ == "__main__":
    main()
