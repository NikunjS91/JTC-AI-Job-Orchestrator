# 1. Event-Driven Microservices Architecture

Date: 2025-11-25

## Status
Accepted

## Context
We are building "CareerOps", a career intelligence platform that needs to process emails, classify them using AI, and generate research briefs. The system must be:
1.  **Resilient**: Failures in AI services shouldn't lose data.
2.  **Scalable**: Able to handle spikes in email volume.
3.  **Observable**: Easy to debug.
4.  **Resource Efficient**: Must run on a local machine with 14GB RAM (no GPU).

## Decision
We will adopt an **Event-Driven Microservices Architecture** within a **Monorepo**.

### 1. Communication: Kafka
- **Why**: Decouples producers (Gmail) from consumers (AI). Allows replayability (7-day retention) if services crash.
- **Topic Structure**:
    - `raw_inbox_stream`: JSON dump of emails.
    - `classified_events`: Enriched events (Interview, Offer).
    - `research_tasks`: Tasks for the research agent.
    - `notifications`: Final alerts for Slack.

### 2. AI Provider: Gemini API
- **Why**: Local LLMs (Ollama) are too heavy for the host machine (14GB RAM).
- **Strategy**: Use Google Gemini API (Flash for speed, Pro for reasoning).
- **Fallback**: Code will support Ollama via a configuration switch, but default to Gemini.

### 3. Repository Structure: Monorepo
- **Why**: Enforces shared standards (logging, config) via `libs/` while keeping services isolated.
- **Structure**:
    - `services/*`: Independent Docker containers.
    - `libs/*`: Shared Python packages.
    - `deploy/*`: Infrastructure definitions.

## Consequences
- **Positive**: High resilience, clear separation of concerns, "production-grade" from day one.
- **Negative**: Higher initial complexity (Docker Compose, Kafka setup) compared to a simple script.
