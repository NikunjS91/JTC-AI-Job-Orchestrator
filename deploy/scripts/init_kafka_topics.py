import os
from kafka.admin import KafkaAdminClient, NewTopic

BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPICS = [
    ("raw_inbox_stream", 1, 1, {"retention.ms": "604800000"}),  # 7 days
    ("classified_events", 1, 1, {"retention.ms": "1209600000"}),  # 14 days
    ("notifications", 1, 1, {"retention.ms": "604800000"}),
    ("dlq.raw_inbox", 1, 1, {"retention.ms": "2592000000"}),  # 30 days
    ("dlq.classified_events", 1, 1, {"retention.ms": "2592000000"}),
    ("dlq.notifications", 1, 1, {"retention.ms": "2592000000"}),
]


def ensure_topics():
    admin = KafkaAdminClient(bootstrap_servers=BROKER, client_id="init-topics")
    existing = set(admin.list_topics())
    to_create = []
    for name, partitions, replication, config in TOPICS:
        if name not in existing:
            to_create.append(NewTopic(name=name, num_partitions=partitions, replication_factor=replication, topic_configs=config))
    if to_create:
        admin.create_topics(new_topics=to_create, validate_only=False)
        print(f"Created topics: {[t.name for t in to_create]}")
    else:
        print("All topics already exist.")


if __name__ == "__main__":
    ensure_topics()
