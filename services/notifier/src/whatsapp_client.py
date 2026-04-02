import requests
from libs.core.config import BaseConfig, get_config
from libs.core.logger import configure_logger

logger = configure_logger("whatsapp_client")

class WhatsAppConfig(BaseConfig):
    WHATSAPP_API_TOKEN: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_RECIPIENT_PHONE: str

config = get_config(WhatsAppConfig)

class WhatsAppClient:
    def __init__(self):
        if not config.WHATSAPP_API_TOKEN:
            logger.error("WHATSAPP_API_TOKEN not found.")
        
        self.api_url = f"https://graph.facebook.com/v17.0/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
        self.headers = {
            "Authorization": f"Bearer {config.WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json"
        }

    def send_notification(self, message: dict):
        if not config.WHATSAPP_API_TOKEN:
            logger.warning("Skipping WhatsApp notification (no token).")
            return

        # Format the message
        body_text = (
            f"🚀 *New Career Event*\n\n"
            f"📅 *Type:* {message.get('event_type')}\n"
            f"🏢 *Company:* {message.get('company')}\n"
            f"🤖 *Confidence:* {message.get('confidence')}\n\n"
            f"📝 *Briefing:*\n{message.get('research_briefing', 'No research available.')[:800]}..." # Truncate for WhatsApp limit
        )

        payload = {
            "messaging_product": "whatsapp",
            "to": config.WHATSAPP_RECIPIENT_PHONE,
            "type": "text",
            "text": {"body": body_text}
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info("Notification sent to WhatsApp.")
        except Exception as e:
            logger.error(f"Failed to send WhatsApp notification: {e}")
            if 'response' in locals():
                logger.error(f"Response: {response.text}")
