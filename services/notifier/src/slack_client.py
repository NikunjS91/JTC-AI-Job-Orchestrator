import requests
from libs.core.config import BaseConfig, get_config
from libs.core.logger import configure_logger

logger = configure_logger("slack_client")

class SlackConfig(BaseConfig):
    SLACK_WEBHOOK_URL: str

config = get_config(SlackConfig)

class SlackClient:
    def __init__(self):
        if not config.SLACK_WEBHOOK_URL:
            logger.error("SLACK_WEBHOOK_URL not found.")
            # In production, raise error

    def send_notification(self, message: dict):
        if not config.SLACK_WEBHOOK_URL:
            logger.warning("Skipping Slack notification (no webhook).")
            return

        payload = {
            "text": f"*New Career Event Detected!* :rocket:\n\n"
                    f"*Type:* {message.get('event_type')}\n"
                    f"*Company:* {message.get('company')}\n"
                    f"*Confidence:* {message.get('confidence')}\n\n"
                    f"*Research Briefing:*\n{message.get('research_briefing', 'No research available.')}"
        }
        
        try:
            response = requests.post(config.SLACK_WEBHOOK_URL, json=payload)
            response.raise_for_status()
            logger.info("Notification sent to Slack.")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
