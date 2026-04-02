# JTC AI Job Orchestrator

Event-driven microservices platform that ingests job-related emails, classifies events with LLMs, enriches company and job insights, and delivers notifications with observability dashboards.

## Why This Project

This project automates high-friction job search workflows:
- Ingest inbound job communications
- Detect event types (interview, offer, rejection, other)
- Enrich records with research context
- Stream updates to downstream services and dashboards
- Expose real-time operational visibility

## Architecture

Core stack:
- Messaging: Kafka and Zookeeper
- Storage: PostgreSQL and MinIO
- Orchestration: Airflow
- Services: ingestion, classifier, researcher, notifier, orchestrator, conversation, dashboard-api, dashboard-ui
- Monitoring: Prometheus and Grafana

Primary runtime config is in deploy/docker-compose.yml.

## Repository Structure

- services: all microservices
- libs/core: shared config, clients, utilities
- deploy: Docker Compose, Airflow DAGs, scripts, monitoring setup
- docs: architecture and implementation references

## Quick Start

1. Create local environment file:

```bash
cp deploy/.env.example deploy/.env
```

2. Fill required secrets in deploy/.env:
- POSTGRES_PASSWORD
- MINIO_ROOT_PASSWORD
- GOOGLE_API_KEY
- GROQ_API_KEY
- OPENAI_API_KEY
- TAVILY_API_KEY
- WHATSAPP_API_TOKEN

3. Start platform:

```bash
cd deploy
docker compose up -d
```

4. Verify core endpoints:

```bash
curl -N http://localhost:8005/events
curl http://localhost:8004/health
```

5. Open dashboards:
- Grafana: http://localhost:3001
- Prometheus: http://localhost:9091
- Airflow: http://localhost:8080

## Security

- Secrets are environment-injected, not hardcoded in Compose.
- Local credential artifacts are gitignored.
- Pre-commit secret scanning is configured with gitleaks.

Enable pre-commit checks:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Useful Commands

```bash
# from deploy directory
cd deploy

# see service status
docker compose ps

# follow logs for one service
docker compose logs -f classifier

# stop stack
docker compose down
```

## Documentation

- docs/architecture-diagram.md
- docs/implementation_plan.md
- docs/PROJECT_STATUS.md

## License

Add a LICENSE file before publishing publicly.
