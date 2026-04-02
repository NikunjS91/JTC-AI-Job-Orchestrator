import time
import json
from kafka import KafkaProducer
from libs.core.logger import configure_logger
from libs.core.config import BaseConfig, get_config
from src.gmail_client import GmailClient
from libs.core.validation import validate_raw_email, compute_dedupe_key_from_email
from prometheus_client import Counter, start_http_server

# Simple in-memory dedupe cache for local runs
_seen_keys = set()

logger = configure_logger("ingestion_service")

# Prometheus metrics
emails_processed = Counter('ingestion_emails_processed_total', 'Total emails processed')
emails_duplicates = Counter('ingestion_emails_duplicates_total', 'Total duplicate emails skipped')
emails_validation_errors = Counter('ingestion_emails_validation_errors_total', 'Total validation errors')
emails_dlq = Counter('ingestion_emails_dlq_total', 'Total emails sent to DLQ')
emails_published = Counter('ingestion_emails_published_total', 'Total emails published to Kafka')

class IngestionConfig(BaseConfig):
    SERVICE_NAME: str = "ingestion"
    POLL_INTERVAL_SECONDS: int = 60

config = get_config(IngestionConfig)

from libs.core.storage import StorageClient

# ... (imports)

def main():
    logger.info("Starting Ingestion Service...")
    
    # Start Prometheus metrics server
    start_http_server(8001)
    logger.info("Prometheus metrics available at :8001/metrics")
    
    # Initialize Clients
    gmail = GmailClient()
    storage = StorageClient(config)
    
    # Initialize Kafka Producer
    producer = None
    try:
        producer = KafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info("Kafka Producer connected.")
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")

    while True:
        logger.info("Polling for new emails...")
        messages = gmail.list_messages(query="is:unread")
        
        for msg in messages:
            msg_id = msg['id']
            full_msg = gmail.get_message(msg_id)
            
            if full_msg:
                emails_processed.inc()
                logger.info(f"Processing message: {msg_id}")

                # Normalize Gmail payload
                payload = {
                    "message_id": full_msg.get("id"),
                    "thread_id": full_msg.get("threadId"),
                    "snippet": full_msg.get("snippet"),
                    "labels": full_msg.get("labelIds"),
                    "source": "gmail",
                    "raw_data": full_msg # Store full raw data in MinIO payload
                }

                # Dedupe
                dedupe_key = compute_dedupe_key_from_email(payload)
                if dedupe_key and dedupe_key in _seen_keys:
                    emails_duplicates.inc()
                    logger.info(f"Skipping duplicate message {msg_id}")
                    continue

                valid, err = validate_raw_email(payload)
                if not valid:
                    emails_validation_errors.inc()
                    logger.error(f"Validation failed for {msg_id}: {err}")
                    if producer:
                        dlq_payload = {"error": "validation_error", "details": err, "original": payload, "source": "ingestion"}
                        producer.send('dlq.raw_inbox', dlq_payload)
                        emails_dlq.inc()
                    continue

                # Upload to MinIO
                try:
                    # Create a path like: 2025/11/26/message_id.json
                    date_prefix = time.strftime("%Y/%m/%d")
                    object_name = f"{date_prefix}/{msg_id}.json"
                    
                    # We upload the FULL raw payload to MinIO
                    storage_path = storage.upload_json(object_name, payload)
                    
                    # We add the storage path to the Kafka payload
                    # And REMOVE the heavy 'raw_data' to keep Kafka light
                    payload['storage_path'] = storage_path
                    if 'raw_data' in payload:
                        del payload['raw_data']
                        
                except Exception as e:
                    logger.error(f"Failed to upload to MinIO: {e}")
                    # Decide: fail hard or continue? For now, we continue but log error
                    # In production, you might want to DLQ this.

                # Publish to Kafka
                if producer:
                    producer.send('raw_inbox_stream', payload)
                    _seen_keys.add(dedupe_key or payload.get("message_id"))
                    emails_published.inc()
                    logger.info(f"Published message {msg_id} to Kafka. Storage: {storage_path}")
                else:
                    logger.warning("Kafka producer not available, skipping publish.")
                
                # Mark as read? (Optional, maybe after successful publish)
                # gmail.mark_as_read(msg_id) 

        time.sleep(config.POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
