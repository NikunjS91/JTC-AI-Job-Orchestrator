# CareerOps: Event-Driven Career Intelligence Platform
## Enterprise System Design Document

**Author:** Senior Data Platform Architect  
**Version:** 1.0  
**Last Updated:** November 2025

---

## Executive Summary

CareerOps is a production-grade, event-driven data platform that transforms career communication chaos into actionable intelligence. Built on the modern data engineering stack (Kafka + Airflow + RAG), it processes 500+ daily emails, extracting the critical 1% of high-signal events (interviews, offers) while autonomously generating competitive intelligence briefings.

**Business Impact:** Reduces Mean Time to Response (MTTR) for interview opportunities from 4+ hours to <5 minutes through automated detection and research pipelines.

---

## System Architecture

### High-Level Design Philosophy

```
[Gmail API] → [Kafka Streams] → [AI Classifiers] → [Research Agents] → [PostgreSQL + Vector DB]
                    ↓                                      ↓
              [Dead Letter Queue]                  [Slack Notifications]
```

    
    subgraph "Kafka Message Bus"
        C --> D[raw_inbox_stream]
        D --> E[classified_events]
        E --> F[research_tasks]
        F --> G[notifications]
        D -.->|Failures| H[dlq_dead_letters]
    end
    
    subgraph "Processing Layer"
        I[Classifier Service<br/>Ollama/Llama3] -->|Consume| D
        I -->|Produce| E
        J[Research Agent<br/>LangChain + Tavily] -->|Consume| E
        J -->|Produce| F
    end
    
    subgraph "Storage Layer"
        K[(PostgreSQL<br/>State Management)]
        L[(ChromaDB<br/>Vector Store)]
        M[S3/MinIO<br/>Raw Emails]
        I --> K
        J --> K
        J --> L
        I --> M
    end
    
    subgraph "Presentation Layer"
        N[Slack Webhook]
        O[Streamlit Dashboard]
        F --> N
        K --> O
    end
    
    style D fill:#ff9999
    style E fill:#99ccff
    style F fill:#99ff99
    style H fill:#ffcc99
```

---

## Critical System Design Decisions

### 1. Event-Driven Architecture with Kafka
**Rationale:** Decouples email ingestion from processing. If the classifier crashes, messages remain in Kafka for replay. Supports horizontal scaling (add more consumers without code changes).

**Alternative Rejected:** Direct API polling → Processing would create tight coupling and lose audit trail.

### 2. Idempotency via Content Hashing
```python
message_hash = SHA256(sender_email + timestamp + subject_line)
```
**Protection Mechanism:** Before processing, check Redis cache. If hash exists, skip to prevent duplicate research tasks costing API credits.

### 3. Rate Limiting with Token Bucket
**Problem:** Ollama inference limited to 5 req/min on commodity hardware.  
**Solution:** Kafka consumer implements token bucket algorithm, batching messages and throttling consumption to prevent service overload.

### 4. Dead Letter Queue (DLQ) Strategy
**Failure Scenarios:**
- Malformed email HTML crashes parser → Route to DLQ
- Ollama service timeout → Retry 3x, then DLQ
- Gmail API rate limit → Exponential backoff, then DLQ

**Monitoring:** Airflow sensor triggers PagerDuty alert if DLQ depth > 10 messages.

---

## Data Flow: Interview Detection Pipeline

**Step-by-Step Execution:**

1. **T+0min:** Gmail webhook fires on new message arrival
2. **T+1min:** Airflow DAG fetches email via Gmail API, publishes to `raw_inbox_stream`
3. **T+2min:** Classifier service consumes message, runs Ollama inference
4. **T+3min:** If classified as `INTERVIEW`, produces event to `classified_events` with metadata:
   ```json
   {
     "event_type": "INTERVIEW",
     "company": "Datadog",
     "scheduled_date": "2025-12-01T14:00:00Z",
     "confidence": 0.94
   }
   ```
5. **T+4min:** Research Agent triggers, calls Tavily API for recent news
6. **T+5min:** LangChain prompt synthesizes briefing doc, stores in ChromaDB
7. **T+5min:** Slack notification sent with briefing link

**SLA:** 95th percentile end-to-end latency < 6 minutes.

---

## Technology Stack Justification

| Component | Choice | Why Not Alternatives? |
|-----------|--------|----------------------|
| **Kafka** | Industry standard for event streaming | RabbitMQ lacks log compaction; AWS SQS not self-hosted |
| **Airflow** | Mature orchestration with DAG visualization | Prefect/Dagster less adopted; cron jobs lack dependency management |
| **PostgreSQL** | ACID guarantees for state transitions | MongoDB lacks strict schemas; DynamoDB vendor lock-in |
| **ChromaDB** | Lightweight vector DB with Python-native API | Pinecone costly; Weaviate overkill for MVP scale |

---

## Operational Excellence

**Observability:**
- Kafka lag monitoring (Alert if consumer lag > 100 messages)
- Prometheus metrics on Ollama inference latency
- Airflow task success rate dashboards

**Disaster Recovery:**
- Kafka retention: 7 days (replay capability)
- PostgreSQL daily backups to S3
- Docker volumes for stateful services

**Security:**
- OAuth2 for Gmail API (no password storage)
- Kafka SASL/SSL in production
- Secrets managed via Docker secrets (not environment variables)

---

## Next Steps: Implementation Roadmap

**Phase 1 (Week 1-2):** Infrastructure - `docker-compose up` runs Kafka + Postgres + Airflow  
**Phase 2 (Week 3-4):** Ingestion + Classification pipeline with DLQ  
**Phase 3 (Week 5-6):** Research Agent with RAG integration  
**Phase 4 (Week 7):** Slack notifications + Streamlit dashboard

**Success Metrics:**
- Process 100 emails/day with zero data loss
- Detect interviews with 90%+ precision
# CareerOps: Event-Driven Career Intelligence Platform
## Enterprise System Design Document

**Author:** Senior Data Platform Architect  
**Version:** 1.0  
**Last Updated:** November 2025

---

## Executive Summary

CareerOps is a production-grade, event-driven data platform that transforms career communication chaos into actionable intelligence. Built on the modern data engineering stack (Kafka + Airflow + RAG), it processes 500+ daily emails, extracting the critical 1% of high-signal events (interviews, offers) while autonomously generating competitive intelligence briefings.

**Business Impact:** Reduces Mean Time to Response (MTTR) for interview opportunities from 4+ hours to <5 minutes through automated detection and research pipelines.

---

## System Architecture

### High-Level Design Philosophy

```
[Gmail API] → [Kafka Streams] → [AI Classifiers] → [Research Agents] → [PostgreSQL + Vector DB]
                    ↓                                      ↓
              [Dead Letter Queue]                  [Slack Notifications]
```

    
    subgraph "Kafka Message Bus"
        C --> D[raw_inbox_stream]
        D --> E[classified_events]
        E --> F[research_tasks]
        F --> G[notifications]
        D -.->|Failures| H[dlq_dead_letters]
    end
    
    subgraph "Processing Layer"
        I[Classifier Service<br/>Ollama/Llama3] -->|Consume| D
        I -->|Produce| E
        J[Research Agent<br/>LangChain + Tavily] -->|Consume| E
        J -->|Produce| F
    end
    
    subgraph "Storage Layer"
        K[(PostgreSQL<br/>State Management)]
        L[(ChromaDB<br/>Vector Store)]
        M[S3/MinIO<br/>Raw Emails]
        I --> K
        J --> K
        J --> L
        I --> M
    end
    
    subgraph "Presentation Layer"
        N[Slack Webhook]
        O[Streamlit Dashboard]
        F --> N
        K --> O
    end
    
    style D fill:#ff9999
    style E fill:#99ccff
    style F fill:#99ff99
    style H fill:#ffcc99
```

---

## Critical System Design Decisions

### 1. Event-Driven Architecture with Kafka
**Rationale:** Decouples email ingestion from processing. If the classifier crashes, messages remain in Kafka for replay. Supports horizontal scaling (add more consumers without code changes).

**Alternative Rejected:** Direct API polling → Processing would create tight coupling and lose audit trail.

### 2. Idempotency via Content Hashing
```python
message_hash = SHA256(sender_email + timestamp + subject_line)
```
**Protection Mechanism:** Before processing, check Redis cache. If hash exists, skip to prevent duplicate research tasks costing API credits.

### 3. Rate Limiting with Token Bucket
**Problem:** Ollama inference limited to 5 req/min on commodity hardware.  
**Solution:** Kafka consumer implements token bucket algorithm, batching messages and throttling consumption to prevent service overload.

### 4. Dead Letter Queue (DLQ) Strategy
**Failure Scenarios:**
- Malformed email HTML crashes parser → Route to DLQ
- Ollama service timeout → Retry 3x, then DLQ
- Gmail API rate limit → Exponential backoff, then DLQ

**Monitoring:** Airflow sensor triggers PagerDuty alert if DLQ depth > 10 messages.

---

## Data Flow: Interview Detection Pipeline

**Step-by-Step Execution:**

1. **T+0min:** Gmail webhook fires on new message arrival
2. **T+1min:** Airflow DAG fetches email via Gmail API, publishes to `raw_inbox_stream`
3. **T+2min:** Classifier service consumes message, runs Ollama inference
4. **T+3min:** If classified as `INTERVIEW`, produces event to `classified_events` with metadata:
   ```json
   {
     "event_type": "INTERVIEW",
     "company": "Datadog",
     "scheduled_date": "2025-12-01T14:00:00Z",
     "confidence": 0.94
   }
   ```
5. **T+4min:** Research Agent triggers, calls Tavily API for recent news
6. **T+5min:** LangChain prompt synthesizes briefing doc, stores in ChromaDB
7. **T+5min:** Slack notification sent with briefing link

**SLA:** 95th percentile end-to-end latency < 6 minutes.

---

## Technology Stack Justification

| Component | Choice | Why Not Alternatives? |
|-----------|--------|----------------------|
| **Kafka** | Industry standard for event streaming | RabbitMQ lacks log compaction; AWS SQS not self-hosted |
| **Airflow** | Mature orchestration with DAG visualization | Prefect/Dagster less adopted; cron jobs lack dependency management |
| **PostgreSQL** | ACID guarantees for state transitions | MongoDB lacks strict schemas; DynamoDB vendor lock-in |
| **ChromaDB** | Lightweight vector DB with Python-native API | Pinecone costly; Weaviate overkill for MVP scale |

---

## Operational Excellence

**Observability:**
- Kafka lag monitoring (Alert if consumer lag > 100 messages)
- Prometheus metrics on Ollama inference latency
- Airflow task success rate dashboards

**Disaster Recovery:**
- Kafka retention: 7 days (replay capability)
- PostgreSQL daily backups to S3
- Docker volumes for stateful services

**Security:**
- OAuth2 for Gmail API (no password storage)
- Kafka SASL/SSL in production
- Secrets managed via Docker secrets (not environment variables)

---

## Next Steps: Implementation Roadmap

**Phase 1 (Week 1-2):** Infrastructure - `docker-compose up` runs Kafka + Postgres + Airflow  
**Phase 2 (Week 3-4):** Ingestion + Classification pipeline with DLQ  
**Phase 3 (Week 5-6):** Research Agent with RAG integration  
**Phase 4 (Week 7):** Slack notifications + Streamlit dashboard

**Success Metrics:**
- Process 100 emails/day with zero data loss
- Detect interviews with 90%+ precision
- Generate research briefs in <5 minutes

---

## Conclusion

CareerOps demonstrates production-level data engineering: fault-tol![CareerOps Architecture](docs/images/architecture.png)erant streaming, intelligent automation, and operational observability. The architecture scales from personal use (1 user) to SaaS (10,000 users) by adding Kafka partitions and consumer groups—no code rewrites required.

**Repository:** [github.com/yourname/careerops]  
**Live Demo:** [Streamlit Cloud Dashboard]