# CareerOps Task List

## 1. Validation & Testing (Immediate Priority)
- [x] **End-to-End Test**: Run `inject_test_event.py` and verify event flow:
    - `raw_inbox_stream` -> `Classifier` -> `classified_events`
- [x] **Verify Kafka**: Ensure local Kafka container is healthy and topics are created.

## 2. Service Refactoring
- [x] **Refactor Researcher Service**:
    - Replace hardcoded `ChatGoogleGenerativeAI` with `LLMClient` (Adapter Pattern).
    - Ensure it supports OpenAI/Groq fallback.
    - Update `research_agent.py` to consume from `classified_events`.

## 3. Dashboard Backend (FastAPI)
- [x] **Create Service**: `services/dashboard-api`
- [x] **Database Connection**: Setup SQLAlchemy/AsyncPG connection to Postgres.
- [x] **API Endpoints**:
    - `GET /events`: List recent career events.
    - `GET /stats`: Return pipeline metrics (emails processed, interviews found).

## 4. Dashboard Frontend (React + Vite)
- [x] **Initialize Project**: `services/dashboard-ui` using Vite.
- [x] **UI Components**: Install Shadcn UI + Tailwind CSS.
- [x] **Views**:
    - **Dashboard**: High-level metrics.
    - **Feed**: List of detected interviews with status.
- [x] **Integration**: Fetch data from FastAPI backend.

## 5. Notifications
- [x] **Slack Integration**:
    - Update `notifier` service to use Slack Webhook URL from `.env`.
    - Format nice message attachments for interviews.

## 6. Deployment & Infrastructure
- [x] **Docker Compose**: Add `dashboard-api` and `dashboard-ui` to `docker-compose.yml`.
- [x] **Environment Variables**: Ensure all new services have correct env vars injected.
