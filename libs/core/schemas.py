from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class RawEmailEvent(BaseModel):
    message_id: str = Field(..., description="Gmail message ID")
    thread_id: Optional[str] = Field(None, description="Gmail thread ID")
    from_email: Optional[str] = None
    to_email: Optional[str] = None
    subject: Optional[str] = None
    received_at: Optional[str] = Field(
        None, description="RFC3339 timestamp when email was received"
    )
    labels: Optional[List[str]] = None
    snippet: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    attachments: Optional[List[Dict[str, str]]] = Field(
        None, description="List of attachments metadata (name, mimeType, size)"
    )
    source: str = Field("gmail", description="Source system identifier")


class ClassifiedEvent(BaseModel):
    event_id: str = Field(..., description="Unique event ID")
    message_id: str = Field(..., description="Upstream Gmail message ID")
    event_type: str = Field(..., description="Type e.g. INTERVIEW, OFFER, OTHER")
    company: Optional[str] = None
    role: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    classified_at: Optional[str] = Field(
        None, description="RFC3339 timestamp when classification was produced"
    )
    metadata: Optional[Dict[str, str]] = None
    research_briefing: Optional[str] = None


class NotificationEvent(BaseModel):
    target_channel: str = Field(..., description="whatsapp, slack")
    payload: Dict[str, str]
    created_at: Optional[str] = None
