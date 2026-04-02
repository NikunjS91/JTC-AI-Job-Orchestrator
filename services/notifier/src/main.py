import json
import time
import requests
from kafka import KafkaConsumer
from libs.core.logger import configure_logger
from libs.core.config import BaseConfig, get_config
from src.whatsapp_client import WhatsAppClient

logger = configure_logger("notifier_service")

class NotifierConfig(BaseConfig):
    SERVICE_NAME: str = "notifier"
    KAFKA_GROUP_ID: str = "notifier_group"
    SLACK_WEBHOOK_URL: str = ""

config = get_config(NotifierConfig)

class SlackClient:
    def __init__(self):
        self.webhook_url = config.SLACK_WEBHOOK_URL
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not set. Slack notifications disabled.")
    
    def send_notification(self, event: dict):
        if not self.webhook_url:
            return

        try:
            # Format message
            event_type = event.get('event_type', 'UNKNOWN')
            company = event.get('company', 'Unknown Company')
            summary = event.get('summary', 'No summary')
            briefing = event.get('research_briefing', '')
            
            color = "#808080"
            if event_type == "INTERVIEW": color = "#36a64f" # Green
            elif event_type == "OFFER": color = "#FFD700" # Gold
            elif event_type == "REJECTION": color = "#FF0000" # Red

            payload = {
                "attachments": [
                    {
                        "color": color,
                        "pretext": f"🚨 New Career Event Detected: *{event_type}*",
                        "title": company,
                        "text": summary,
                        "fields": [
                            {
                                "title": "Confidence",
                                "value": f"{event.get('confidence', 0)*100:.0f}%",
                                "short": True
                            }
                        ],
                        "footer": "CareerOps AI",
                        "ts": int(time.time())
                    }
                ]
            }
            
            if briefing:
                payload["attachments"].append({
                    "color": "#439FE0",
                    "title": "Research Briefing",
                    "text": briefing
                })

            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            logger.info(f"Sent Slack notification for {company}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

def main():
    logger.info("Starting Notifier Service...")
    
    whatsapp = WhatsAppClient()
    slack = SlackClient()
    
    # Wait for Kafka
    consumer = None
    while not consumer:
        try:
            consumer = KafkaConsumer(
                'notifications',
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=config.KAFKA_GROUP_ID,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='earliest'
            )
            logger.info("Kafka Consumer connected.")
        except Exception as e:
            logger.warning(f"Waiting for Kafka... {e}")
            time.sleep(5)
    
    logger.info("Listening for notifications...")
    
    for message in consumer:
        event = message.value
        logger.info(f"Received notification for: {event.get('company')}")
        
        # Send to all configured channels
        whatsapp.send_notification(event)
        slack.send_notification(event)

if __name__ == "__main__":
    main()
