import json
from kafka import KafkaConsumer
from libs.core.config import BaseConfig, get_config

class Config(BaseConfig):
    SERVICE_NAME: str = "test_reader"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

config = get_config(Config)

def read_events():
    print("Connecting to Kafka...")
    consumer = KafkaConsumer(
        'classified_events',
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        consumer_timeout_ms=5000  # Stop after 5s if no messages
    )
    
    print("Reading messages...")
    for message in consumer:
        try:
            val = json.loads(message.value.decode('utf-8'))
            if val.get('original_email_id') == 'test_email_123':
                print("✅ Found test event!")
                break
        except:
            pass

if __name__ == "__main__":
    read_events()
