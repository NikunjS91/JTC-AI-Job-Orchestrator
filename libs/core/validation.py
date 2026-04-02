from typing import Tuple, Optional
from libs.core.schemas import RawEmailEvent, ClassifiedEvent


def validate_raw_email(payload: dict) -> Tuple[bool, Optional[str]]:
    """Validate incoming raw email payload against RawEmailEvent schema."""
    try:
        RawEmailEvent(**payload)
        return True, None
    except Exception as e:
        return False, str(e)


def validate_classified_event(payload: dict) -> Tuple[bool, Optional[str]]:
    """Validate classified event payload against ClassifiedEvent schema."""
    try:
        ClassifiedEvent(**payload)
        return True, None
    except Exception as e:
        return False, str(e)


def compute_dedupe_key_from_email(payload: dict) -> Optional[str]:
    """Return a stable dedupe key from Gmail message/thread IDs."""
    msg_id = payload.get("message_id")
    thread_id = payload.get("thread_id")
    if msg_id or thread_id:
        return f"{thread_id or ''}:{msg_id or ''}"
    return None
