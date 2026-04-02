# Cloud Service Evaluation Prompt for CareerOps Platform

## **Copy-Paste This to ChatGPT/Claude/Gemini:**

---

I need to deploy an **event-driven microservices platform** to a free/low-cost cloud provider. Please analyze my architecture and recommend the best free-tier cloud service.

## **System Architecture:**

### **Services to Deploy (4 Microservices):**
1. **Ingestion Service** (Python 3.9)
   - Memory: ~150MB RAM
   - CPU: Low (polls Gmail API every 60s)
   - Dependencies: `google-api-python-client`, `kafka-python`
   - Needs: Persistent storage for `token.pickle` (OAuth token)

2. **Classifier Service** (Python 3.9)
   - Memory: ~200MB RAM
   - CPU: Medium (LLM API calls, 1 request every 9 minutes)
   - Dependencies: `openai`, `groq`, `google-generativeai`, `kafka-python`
   - External APIs: OpenAI, Groq, Gemini (no local ML models)

3. **Researcher Service** (Python 3.9)
   - Memory: ~200MB RAM
   - CPU: Low (Tavily API calls, 1 request every 55 minutes)
   - Dependencies: `langchain`, `tavily-python`, `kafka-python`

4. **Notifier Service** (Python 3.9)
   - Memory: ~150MB RAM
   - CPU: Very Low (HTTP POST to WhatsApp API)
   - Dependencies: `requests`, `kafka-python`

### **Infrastructure Requirements:**

**Message Broker:**
- Apache Kafka + Zookeeper
- Memory: ~450MB combined
- Storage: ~1GB for message retention (7 days)
- 3 Topics: `raw_inbox_stream`, `classified_events`, `notifications`

**Database:**
- PostgreSQL 13
- Memory: ~100MB
- Storage: ~500MB (minimal usage, only Airflow metadata)

**Orchestration (Optional):**
- Apache Airflow (Scheduler + Webserver)
- Memory: ~300MB combined
- Only needed if running scheduled DAGs

**Total Resource Requirements:**
- **Minimum:** 1GB RAM (without Airflow) for 4 services + Kafka + PostgreSQL
- **Recommended:** 2GB RAM (with Airflow)
- **Storage:** 2-3GB persistent disk
- **Network:** Minimal (API calls only, no high throughput)

### **Technical Constraints:**
- **Docker-based:** All services containerized (`docker-compose.yml` available)
- **Stateless Services:** Services can restart without data loss (Kafka handles state)
- **No GPU:** All AI processing via external APIs (OpenAI/Gemini/Groq)
- **Low Traffic:** Processes ~160-800 emails/day (1 every 9 minutes due to rate limiting)
- **Persistent Storage Needed:** 
  - Gmail OAuth token (`token.pickle`)
  - Kafka message logs (2-3 days retention)
  - PostgreSQL data

### **Current Deployment Method:**
- `docker-compose.yml` with 11 containers (can be reduced to 6 if removing optional services)
- Environment variables managed via `.env` file
- No Kubernetes (but can migrate if required)

---

## **Evaluation Criteria (Rank by Importance):**

1. **Free Tier Limits:**
   - RAM/CPU allocation
   - Persistent storage (GB)
   - Monthly hours/credits
   - Egress bandwidth limits

2. **Kafka Compatibility:**
   - Can I run Kafka in a container? (Deal-breaker if no)
   - OR: Managed Kafka service in free tier?
   - OR: Alternative message queue (Redis Streams, RabbitMQ) that works better?

3. **Database Support:**
   - PostgreSQL included in free tier?
   - OR: External free DB (Supabase, Neon, etc.) compatible?

4. **Docker Support:**
   - Native Docker/Docker Compose support?
   - OR: Need to convert to platform-specific config (Kubernetes, Cloud Run, etc.)?

5. **Persistent Storage:**
   - File storage for `token.pickle` that survives restarts?
   - Volume mounting support?

6. **Deployment Complexity:**
   - How easy to deploy from `docker-compose.yml`?
   - CLI/API available for automation?

7. **Monitoring & Logs:**
   - Free tier includes logs retention?
   - Prometheus/Grafana support?

8. **Networking:**
   - Can containers talk to each other (internal network)?
   - Webhooks/incoming requests supported?

---

## **Platforms to Compare:**

Please evaluate these platforms and rank them for my use case:

1. **Railway** (railway.app)
2. **Render** (render.com)
3. **Fly.io** (fly.io)
4. **Google Cloud Run** (Free tier)
5. **AWS ECS/Fargate** (Free tier)
6. **Azure Container Instances** (Free tier)
7. **Heroku** (Eco/Free tier)
8. **DigitalOcean App Platform** (Free tier)
9. **Vercel** (for serverless approach)
10. **Supabase + Cloudflare Workers** (hybrid approach)

---

## **Specific Questions:**

1. **Can Kafka run in free tier?** If not, what's the best lightweight alternative (Redis Streams, RabbitMQ, AWS SQS)?

2. **Docker Compose vs Kubernetes:** Should I:
   - Deploy `docker-compose.yml` directly? (Railway, Render)
   - Convert to Kubernetes manifests? (GKE, EKS free tier)
   - Rewrite as serverless functions? (Vercel, Cloudflare Workers)

3. **Database Strategy:** Better to:
   - Use platform's managed PostgreSQL? (if available in free tier)
   - Use external free DB (Neon, Supabase, PlanetScale)?
   - Embed SQLite in containers? (loses Kafka metadata on restart)

4. **Cost After Free Tier:** If I exceed free tier limits, which platform has:
   - Most generous pay-as-you-go pricing?
   - Easiest to scale horizontally (add more containers)?

5. **Best for Portfolio/Resume:** Which platform would impress interviewers most?
   - "Deployed on Railway" (ease of use)
   - "Deployed on GCP Cloud Run" (cloud-native cred)
   - "Deployed on Fly.io" (hacker credibility)

---

## **Output Format:**

Please provide:

1. **Top 3 Recommended Platforms** (ranked)
2. **Pros/Cons Table** for each
3. **Architecture Modifications Needed** (e.g., "Replace Kafka with Redis Streams on Render")
4. **Deployment Steps** (high-level) for #1 recommendation
5. **Free Tier Limits Summary** (RAM, storage, hours/month)
6. **Estimated Monthly Cost** if I exceed free tier by 20%

---

## **Bonus: Alternative Architecture:**

If running Kafka is impossible in free tier, suggest:
- Best lightweight message queue alternative?
- Could I use managed services (AWS SQS, GCP Pub/Sub free tier)?
- Should I switch to webhook-based architecture (no message queue)?

---

**Expected Response:**
A detailed comparison table + clear recommendation with migration steps.

Thank you!
