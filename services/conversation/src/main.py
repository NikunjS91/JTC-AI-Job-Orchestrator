from fastapi import FastAPI, HTTPException, Request, Query

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from prometheus_client import Counter, make_asgi_app
from libs.core.logger import configure_logger
from libs.core.config import BaseConfig, get_config
import time
from kafka import KafkaProducer
import json
from libs.core.db import DatabaseClient, Application

logger = configure_logger("conversation_service")

# Prometheus metrics
intents_processed = Counter('conversation_intents_processed_total', 'Total intents processed', ['intent_type'])
intent_errors = Counter('conversation_intent_errors_total', 'Total intent processing errors')

class ConversationConfig(BaseConfig):
    SERVICE_NAME: str = "conversation"
    WHATSAPP_VERIFY_TOKEN: str = "my_secure_token"  # Default, override in env

config = get_config(ConversationConfig)

app = FastAPI(title="Conversation Agent API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Simple in-memory session store (replace with Redis for production)
sessions: Dict[str, Dict[str, Any]] = {}

class IntentRequest(BaseModel):
    intent: str
    session_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class IntentResponse(BaseModel):
    response: str
    data: Optional[Dict[str, Any]] = None
    session_id: str

@app.get("/health")
async def health():
    return {"status": "ok", "ts": time.time()}

from libs.core.llm_client import LLMClient



# Initialize Clients
try:
    db = DatabaseClient(config)
except Exception as e:
    logger.error(f"DB Init failed: {e}")
    db = None

producer = None
try:
    producer = KafkaProducer(
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
except Exception as e:
    logger.error(f"Kafka Init failed: {e}")

# Initialize LLM Client
llm_client = None
try:
    llm_client = LLMClient()
    logger.info("LLM Client initialized for Semantic Router")
except Exception as e:
    logger.warning(f"LLM Client init failed (Semantic Router will be disabled): {e}")

def semantic_router(user_message: str) -> dict:
    """
    Use LLM to map natural language to structured intent.
    """
    if not llm_client:
        return {"intent": "unknown", "parameters": {}}
        
    prompt = f"""You are a semantic router for a Career Dashboard.
Map the user's message to one of the following JSON intents:

1. stats_today
   - User asks for today's numbers, daily stats, or status.
   - Output: {{"intent": "stats_today", "parameters": {{}}}}

2. summarize_last
   - User asks for a summary of recent events, what happened lately, or last N items.
   - Output: {{"intent": "summarize_last", "parameters": {{"count": 5}}}} (default count to 5 if not specified)

3. research_company
   - User asks to research, analyze, or look up a specific company.
   - Output: {{"intent": "research_company", "parameters": {{"company": "CompanyName"}}}}

4. unknown
   - If the message doesn't fit any of the above.
   - Output: {{"intent": "unknown", "parameters": {{}}}}

User Message: "{user_message}"

Return ONLY the JSON object.
"""
    try:
        response_text = llm_client.generate_text(prompt)
        # Clean up potential markdown code blocks
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        return json.loads(response_text)
    except Exception as e:
        logger.error(f"Semantic Router failed: {e}")
        return {"intent": "unknown", "parameters": {}}

@app.get("/webhook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """
    Meta (Facebook) Webhook Verification Challenge
    """
    if mode == "subscribe" and token == config.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully!")
        return int(challenge)
    
    logger.warning(f"Webhook verification failed. Token: {token}")
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Handle inbound WhatsApp messages
    """
    try:
        payload = await request.json()
        logger.info(f"Received webhook payload: {json.dumps(payload)}")
        
        # Extract message
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return {"status": "ignored", "reason": "no_messages"}
            
        msg = messages[0]
        from_number = msg.get("from")
        msg_body = msg.get("text", {}).get("body", "")
        
        if not msg_body:
            return {"status": "ignored", "reason": "no_text_body"}
            
        logger.info(f"WhatsApp Message from {from_number}: {msg_body}")
        
        # Route intent
        # We use a session ID based on the phone number to keep context
        session_id = f"wa_{from_number}"
        
        # Use Semantic Router
        routed = semantic_router(msg_body)
        intent = routed.get("intent", "unknown")
        params = routed.get("parameters", {})
        
        # Execute Intent (Reuse logic by creating internal request)
        # In a cleaner architecture, we'd extract the logic from process_intent into a controller.
        # For now, we'll just call the logic directly or via internal API call if needed.
        # But since we are inside the same app, let's just call a helper.
        
        response_data = await execute_intent_logic(intent, params, session_id)
        
        # TODO: Send response back to WhatsApp via Graph API
        # For now, just log it
        logger.info(f"Generated Response for WhatsApp: {response_data.get('response')}")
        
        return {"status": "processed", "response": response_data.get("response")}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        # Return 200 to prevent Meta from retrying endlessly
        return {"status": "error", "detail": str(e)}

async def execute_intent_logic(intent: str, params: dict, session_id: str) -> dict:
    """
    Helper to execute intent logic (extracted from process_intent)
    """
    try:
        if intent == "stats_today":
            intents_processed.labels(intent_type="stats_today").inc()
            
            if not db:
                return {"response": "Database unavailable."}
                
            session = db.Session()
            try:
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                apps = session.query(Application).filter(Application.created_at >= today_start).all()
                
                interviews = sum(1 for a in apps if a.status == 'INTERVIEW')
                offers = sum(1 for a in apps if a.status == 'OFFER')
                rejections = sum(1 for a in apps if a.status == 'REJECTION')
                
                response_text = f"📊 *Today's Stats*:\n\n• Interviews: {interviews}\n• Offers: {offers}\n• Rejections: {rejections}\n\nTotal: {len(apps)}"
                return {"response": response_text}
            finally:
                session.close()
                
        elif intent == "summarize_last":
            intents_processed.labels(intent_type="summarize_last").inc()
            if not db: return {"response": "Database unavailable."}

            count = params.get("count", 5)
            session = db.Session()
            try:
                apps = session.query(Application).order_by(Application.created_at.desc()).limit(count).all()
                if not apps:
                    return {"response": "No recent events found."}
                
                lines = []
                for app in apps:
                    icon = "📝"
                    if app.status == 'INTERVIEW': icon = "📅"
                    elif app.status == 'OFFER': icon = "🎉"
                    elif app.status == 'REJECTION': icon = "❌"
                    lines.append(f"{icon} *{app.company}* ({app.role})")
                
                return {"response": f"Last {len(apps)} events:\n\n" + "\n".join(lines)}
            finally:
                session.close()
                
        elif intent == "research_company":
            intents_processed.labels(intent_type="research_company").inc()
            company = params.get("company")
            if not company: return {"response": "Which company?"}
            
            if producer:
                event = {
                    "event_id": f"manual_{int(time.time())}",
                    "event_type": "MANUAL_RESEARCH",
                    "company": company,
                    "role": "General",
                    "confidence": 1.0,
                    "classified_at": datetime.utcnow().isoformat(),
                    "summary": "Manual research request from WhatsApp",
                    "metadata": {"source": "whatsapp"}
                }
                producer.send('classified_events', event)
                return {"response": f"🔍 Queued research for *{company}*."}
            else:
                return {"response": "Kafka unavailable."}
        
        else:
            return {"response": "I didn't understand that. Try 'stats' or 'research [company]'."}
            
    except Exception as e:
        logger.error(f"Logic error: {e}")
        return {"response": "Error executing command."}

@app.post("/intent", response_model=IntentResponse)
async def process_intent(request: IntentRequest):
    """
    Process conversational intents for both Dashboard and WhatsApp
    """
    
    session_id = request.session_id or f"session_{int(time.time())}"
    intent = request.intent.lower()
    params = request.parameters or {}
    
    # If intent is "natural_language" or "unknown", try Semantic Router
    if intent in ["natural_language", "unknown"] and params.get("message"):
        logger.info(f"Routing natural language: {params['message']}")
        routed = semantic_router(params['message'])
        intent = routed.get("intent", "unknown")
        params = routed.get("parameters", {})
        logger.info(f"Routed to: {intent} with params: {params}")
    
    logger.info(f"Processing intent: {intent} for session: {session_id}")
    
    # Reuse the logic helper
    result = await execute_intent_logic(intent, params, session_id)
    
    return {
        "response": result.get("response"),
        "data": {},
        "session_id": session_id
    }

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return sessions[session_id]

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Conversation Service...")
    uvicorn.run(app, host="0.0.0.0", port=8004)
