import json
import time
from kafka import KafkaProducer
from libs.core.config import BaseConfig, get_config

class Config(BaseConfig):
    SERVICE_NAME: str = "test_injector"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

config = get_config(Config)

def inject_event():
    producer = KafkaProducer(
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    # Simulate a VERY CLEAR interview email
    # Simulate a VERY CLEAR interview email matching RawEmailEvent schema
    fake_email = {
        "message_id": f"test_interview_{int(time.time())}",
        "thread_id": f"thread_{int(time.time())}",
        "from_email": "recruiting@google.com",
        "to_email": "me@example.com",
        "subject": "Interview Invitation - Google Careers",
        "received_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "snippet": "Congratulations! We would like to invite you for an interview at Google for the Senior Software Engineer position.",
        "body_text": "Dear Candidate, We are impressed with your application matches.",
        "source": "gmail"
    }
    
    print(f"Injecting test email: {fake_email['message_id']}")
    producer.send('raw_inbox_stream', fake_email)
    producer.flush()
    print("Event injected successfully!")

if __name__ == "__main__":
    inject_event()
