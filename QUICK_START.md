# Quick Start Guide - Hybrid Architecture

## Prerequisites
- Docker and Docker Compose installed
- Python 3.11+ (for local testing)
- Gmail credentials (credentials.json and token.pickle)

---

## 🚀 Quick Start (5 Minutes)

### 1. Start Infrastructure
```bash
cd deploy
docker-compose up -d zookeeper kafka postgres minio
```

Wait 30 seconds for services to be healthy.

### 2. Initialize Kafka Topics
```bash
python ../deploy/scripts/init_kafka_topics.py
```

### 3. Start All Services
```bash
docker-compose up -d
```

### 4. Verify Services
```bash
# Check all services are running
docker-compose ps

# Check orchestrator SSE
curl -N http://localhost:8005/events

# Check conversation agent
curl http://localhost:8004/health

# Check Prometheus targets
open http://localhost:9090/targets
```

---

## 📊 Access Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3001 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |
| **Airflow** | http://localhost:8080 | - |
| **Dashboard UI** | http://localhost:3000 | - |
| **MinIO Console** | http://localhost:9001 | minio_admin/minio_password |

---

## 🧪 Testing Components

### Test Prometheus Metrics
```bash
# Ingestion metrics
curl http://localhost:8001/metrics | grep ingestion_

# Classifier metrics
curl http://localhost:8002/metrics | grep classifier_

# Researcher metrics
curl http://localhost:8003/metrics | grep researcher_

# Orchestrator metrics
curl http://localhost:8005/metrics | grep orchestrator_

# Conversation metrics
curl http://localhost:8004/metrics | grep conversation_
```

### Test SSE Stream
```bash
# Terminal 1: Listen to SSE
curl -N http://localhost:8005/events

# Terminal 2: Inject test event
python inject_test_event.py
```

### Test Conversation Agent
```bash
# Get today's stats
curl -X POST http://localhost:8004/intent \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "stats_today",
    "session_id": "test_session_1"
  }'

# Summarize last 5 events
curl -X POST http://localhost:8004/intent \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "summarize_last",
    "parameters": {"count": 5},
    "session_id": "test_session_1"
  }'

# Research a company
curl -X POST http://localhost:8004/intent \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "research_company",
    "parameters": {"company": "Google"},
    "session_id": "test_session_1"
  }'
```

### Test Daily Stats Job
```bash
# Run manually
python deploy/scripts/daily_stats_job.py

# Check it published to Kafka
python read_test_events.py
```

---

## 📈 Monitoring

### View Metrics in Grafana
1. Open http://localhost:3001
2. Login with admin/admin
3. Import dashboard: `deploy/grafana/dashboards/microservices_overview.json`
4. View real-time metrics

### Key Metrics to Watch
- **Ingestion:** Emails processed, duplicates, validation errors
- **Classifier:** Events classified by type, rate limits
- **Researcher:** Research completed/failed, rate limits
- **Orchestrator:** SSE connections, events streamed
- **Conversation:** Intents processed by type
- **DLQ:** Messages in dead letter queues

---

## 🔍 Debugging

### View Service Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f orchestrator
docker-compose logs -f conversation
docker-compose logs -f classifier

# Last 100 lines
docker-compose logs --tail=100 ingestion
```

### Check Kafka Topics
```bash
# List topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:29092

# Read from notifications topic
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:29092 \
  --topic notifications \
  --from-beginning
```

### Check Prometheus Scraping
```bash
# View targets status
curl http://localhost:9090/api/v1/targets | jq

# Query specific metric
curl 'http://localhost:9090/api/v1/query?query=ingestion_emails_processed_total'
```

---

## 🛠️ Common Operations

### Restart a Service
```bash
docker-compose restart orchestrator
```

### Rebuild a Service
```bash
docker-compose build orchestrator
docker-compose up -d orchestrator
```

### Scale Services (if needed)
```bash
# Not recommended for stateful services, but possible
docker-compose up -d --scale classifier=2
```

### Clean Up
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

---

## 📝 Configuration

### Environment Variables
Edit `deploy/.env` or `deploy/docker-compose.yml`:

```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:29092

# Postgres
DATABASE_URL=postgresql://airflow:airflow_password@postgres:5432/airflow

# API Keys (already configured)
GOOGLE_API_KEY=...
GROQ_API_KEY=...
TAVILY_API_KEY=...
WHATSAPP_API_TOKEN=...
```

### Prometheus Scrape Interval
Edit `deploy/prometheus/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s  # Change to desired interval
```

---

## 🎯 End-to-End Test Flow

### Complete Pipeline Test
1. **Send test email** (or wait for real Gmail)
2. **Ingestion** processes → publishes to `raw_inbox_stream`
3. **Classifier** consumes → classifies → publishes to `classified_events`
4. **Researcher** consumes → researches → publishes to `notifications`
5. **Orchestrator** consumes → streams via SSE
6. **Notifier** consumes → sends to Slack/WhatsApp
7. **Check metrics** in Grafana

### Verify Each Step
```bash
# 1. Check ingestion metrics
curl http://localhost:8001/metrics | grep published

# 2. Check classifier metrics
curl http://localhost:8002/metrics | grep classified

# 3. Check researcher metrics
curl http://localhost:8003/metrics | grep completed

# 4. Check orchestrator SSE
curl -N http://localhost:8005/events

# 5. Check Grafana dashboard
open http://localhost:3001
```

---

## 🚨 Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs service_name

# Common issues:
# - Kafka not ready → wait 30s after starting
# - Port conflict → check if port already in use
# - Missing env vars → check .env file
```

### No Metrics in Prometheus
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check service metrics endpoint directly
curl http://localhost:8001/metrics

# Verify prometheus.yml configuration
cat deploy/prometheus/prometheus.yml
```

### SSE Not Streaming
```bash
# Check orchestrator logs
docker-compose logs orchestrator

# Verify Kafka notifications topic has data
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:29092 \
  --topic notifications \
  --from-beginning

# Test with curl
curl -N http://localhost:8005/events
```

### Conversation Agent Errors
```bash
# Check logs
docker-compose logs conversation

# Test health endpoint
curl http://localhost:8004/health

# Verify intent format
curl -X POST http://localhost:8004/intent \
  -H "Content-Type: application/json" \
  -d '{"intent": "stats_today"}'
```

---

## 📚 Additional Resources

- **Architecture Diagram:** `architecture-planning.md` Section 6
- **Implementation Details:** `IMPLEMENTATION_COMPLETE.md`
- **Progress Log:** `llm-conversation/progress.md`
- **Grafana Dashboard:** `deploy/grafana/dashboards/microservices_overview.json`

---

## ✅ Health Check Checklist

Run this to verify everything is working:

```bash
# 1. Infrastructure
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:8080/health     # Airflow

# 2. Services
curl http://localhost:8001/metrics    # Ingestion
curl http://localhost:8002/metrics    # Classifier
curl http://localhost:8003/metrics    # Researcher
curl http://localhost:8005/health     # Orchestrator
curl http://localhost:8004/health     # Conversation

# 3. SSE Stream
curl -N http://localhost:8005/events  # Should show heartbeats

# 4. Conversation Agent
curl -X POST http://localhost:8004/intent \
  -H "Content-Type: application/json" \
  -d '{"intent": "stats_today"}'
```

If all return 200 OK, you're good to go! 🎉

---

**Last Updated:** 2025-11-26
