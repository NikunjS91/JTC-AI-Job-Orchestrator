"""
Daily Stats Job - Computes end-of-day statistics and sends notifications

This can be run via cron or Airflow DAG
"""
import json
import time
from datetime import datetime, timedelta
from kafka import KafkaProducer
from libs.core.logger import configure_logger
from libs.core.config import BaseConfig, get_config

logger = configure_logger("daily_stats_job")

class StatsConfig(BaseConfig):
    SERVICE_NAME: str = "daily_stats"

config = get_config(StatsConfig)

def compute_daily_stats():
    """
    Compute statistics for the day
    
    TODO: Query Postgres for actual stats
    For now, returns placeholder data
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    # TODO: Replace with actual Postgres queries
    stats = {
        "date": today,
        "interviews": 0,
        "offers": 0,
        "rejections": 0,
        "total_events": 0,
        "top_companies": [],
        "pending_actions": 0
    }
    
    logger.info(f"Computed stats for {today}: {stats}")
    return stats

def send_daily_summary(stats: dict):
    """Send daily summary via Kafka notifications topic"""
    
    try:
        producer = KafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Format as notification event
        notification = {
            "event_type": "DAILY_SUMMARY",
            "company": "CareerOps System",
            "role": "Daily Report",
            "confidence": 1.0,
            "summary": format_summary_message(stats),
            "metadata": stats,
            "research_briefing": "",
            "classified_at": datetime.now().isoformat(),
            "event_id": f"daily_summary_{stats['date']}"
        }
        
        producer.send('notifications', notification)
        producer.flush()
        
        logger.info(f"Sent daily summary to notifications topic")
        
    except Exception as e:
        logger.error(f"Failed to send daily summary: {e}")

def format_summary_message(stats: dict) -> str:
    """Format stats into a readable message"""
    
    msg = f"📊 Daily Summary for {stats['date']}\n\n"
    msg += f"• Interviews: {stats['interviews']}\n"
    msg += f"• Offers: {stats['offers']}\n"
    msg += f"• Rejections: {stats['rejections']}\n"
    msg += f"• Total Events: {stats['total_events']}\n"
    
    if stats['top_companies']:
        msg += f"\n🏢 Top Companies:\n"
        for company in stats['top_companies'][:5]:
            msg += f"  • {company}\n"
    
    if stats['pending_actions'] > 0:
        msg += f"\n⚠️ Pending Actions: {stats['pending_actions']}\n"
    
    return msg

def main():
    logger.info("Starting Daily Stats Job...")
    
    # Compute stats
    stats = compute_daily_stats()
    
    # Send summary
    send_daily_summary(stats)
    
    logger.info("Daily Stats Job completed successfully")

if __name__ == "__main__":
    main()
