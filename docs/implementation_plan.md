# Implementation Plan - Phase 0 & 1: Production Architecture Setup

## Goal Description
Establish a production-grade, event-driven architecture for CareerOps. This plan moves beyond a simple "script" approach to a robust, scalable microservices-ready structure using Domain-Driven Design (DDD) principles. We will ensure fail-safe mechanisms (DLQs, Circuit Breakers), comprehensive observability, and strict separation of concerns.

## User Review Required
> [!IMPORTANT]
> **Architectural Shift**: We are moving to a **Monorepo** structure. This adds initial complexity but ensures shared standards (logging, config, schemas) across all services.
>
> **Key Decisions**:
> 1. **Shared Libraries**: A `libs/` directory will house standardized wrappers for Kafka, Logging, and Configuration to enforce consistency.
> 2. **Service Isolation**: Each domain (Ingestion, Classification, Research) will be an isolated service with its own Dockerfile and dependency management.
> 3. **Infrastructure as Code**: Explicit separation of local dev (`docker-compose`) from production manifests (`deploy/`).

> [!WARNING]
> **System Resource Alert**: Your system has ~14GB RAM and no dedicated GPU.
> Running the full stack (Kafka + Airflow + LLM) locally will be tight.
> **Mitigation**:
> 1. **Primary Strategy**: We will use **Gemini API** (Flash/Pro) for Classification and Research. This offloads the heavy compute from your local machine to Google's cloud, ensuring the system runs smoothly on 14GB RAM.
> 2. **Secondary Strategy**: We will keep Ollama configuration as a local fallback, but default to Gemini.

## Proposed Changes

### 1. Directory Structure (Monorepo)

```text
CareerOps/
├── .github/                # CI/CD Workflows
├── deploy/                 # IaC (Terraform/K8s) & Docker Compose
│   ├── docker-compose.yml  # Local development orchestration
│   └── prometheus/         # Observability configs
├── docs/
│   └── adr/                # Architecture Decision Records
├── libs/                   # Shared internal libraries
│   ├── core/               # Logging (structlog), Config (Pydantic), Utils
│   └── messaging/          # Kafka Producer/Consumer wrappers with OTEL
├── services/               # Microservices (DDD)
│   ├── ingestion/          # Gmail Poller -> Kafka
│   ├── classifier/         # Event Stream -> Gemini/Ollama -> Event Stream
│   ├── researcher/         # Event Stream -> Gemini/RAG -> Event Stream
│   └── notifier/           # Event Stream -> Slack/Email
├── platform/               # Data Platform Components
│   └── airflow/            # DAGs and Plugins
├── tests/                  # End-to-End & Integration Tests
├── Makefile                # Unified build/run commands
└── pyproject.toml          # Monorepo dependency management (Poetry/Rye)
```

### 2. Infrastructure Definition (`deploy/docker-compose.yml`)
We will enhance the stack to include observability and resilience:
- **Message Bus**: Kafka + Zookeeper + *Schema Registry* (for strict contract enforcement).
- **Observability**: Prometheus (metrics), Grafana (dashboards), Jaeger (tracing).
- **Storage**: PostgreSQL (Application DB), MinIO (Object Store), ChromaDB (Vector Store).
- **Orchestration**: Airflow (managed via extended Docker image).

### 3. Shared Core Library (`libs/core`)
Before building services, we define the "Golden Path":
- **Structured Logging**: JSON logging with trace IDs injected automatically.
- **Configuration**: Environment-aware config loading using Pydantic Settings.
- **Resilience**: Standardized retry decorators and circuit breaker patterns.

## Verification Plan

### Automated Verification
- **Structure Check**: Script to verify all directories and `__init__.py` files exist.
- **Infrastructure Boot**: `make up` (wraps docker-compose) brings up the full stack including observability.
- **Health Checks**: Verify `/health` endpoints on all infrastructure containers.

### Manual Verification
- Review the `docs/adr/001-event-driven-architecture.md` (to be created) to ensure alignment on the architectural vision.
