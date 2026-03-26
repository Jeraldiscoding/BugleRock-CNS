import sqlite3
import json
import logging
from datetime import datetime, timedelta
from meeting_intelligence import MeetingInsights

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ==========================================
# Zoho CRM Integration (Mocks)
# ==========================================
def sync_to_zoho(insights: MeetingInsights, contact_id: str, deal_id: str = None) -> bool:
    """
    Syncs the Claude-extracted meeting insights to the Zoho CRM.
    - Maps decisions_made -> Zoho Notes
    - Maps commitments_given -> Zoho Tasks (Due in 3 days)
    """
    logger.info(f"Starting Zoho sync for contact {contact_id}")
    
    # Map decisions to Zoho Notes
    if insights.decisions_made:
        notes_content = "Meeting Decisions:\n- " + "\n- ".join(insights.decisions_made)
        # Mock Zoho API call for Notes
        logger.info(f"Mock Zoho API -> Created Note for Contact {contact_id}: \n{notes_content}")
    else:
        logger.info(f"No decisions extracted for contact {contact_id}, skipping Notes creation.")

    # Map commitments to Zoho Tasks
    if insights.commitments_given:
        due_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        for idx, commitment in enumerate(insights.commitments_given):
            # Mock Zoho API call for Tasks
            logger.info(f"Mock Zoho API -> Created Task for Contact {contact_id} | Due: {due_date} | Action: {commitment}")
    else:
        logger.info(f"No commitments extracted for contact {contact_id}, skipping Tasks creation.")
        
    logger.info(f"Zoho sync completed for contact {contact_id}.")
    return True


# ==========================================
# Universal Router Event Publishing
# ==========================================
def publish_meeting_event(insights: MeetingInsights, metadata: dict, db_path: str = "universal_router.db"):
    """
    Publishes the 'meeting_analysed' event to the SQLite event bus.
    Payload includes risk_flags, sentiment_shift, and contact/deal IDs.
    """
    event_type = "meeting_analysed"
    
    # Construct the JSON payload containing the analytical data and the routing IDs
    payload_dict = {
        "risk_flags": insights.risk_flags,
        "sentiment_shift": insights.sentiment_shift,
        "zoho_contact_id": metadata.get("zoho_contact_id", "unknown"),
        "company_name": metadata.get("company_name", "unknown")
    }
    
    payload_json = json.dumps(payload_dict)
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    try:
        # We connect to the parent directory where universal_router.db resides
        import os
        # Ensure we look in the right place relative to this file
        real_db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path)
        
        with sqlite3.connect(real_db_path) as conn:
            cursor = conn.cursor()
            
            # Ensure the table exists just in case it's dropped
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT DEFAULT 'unread'
                )
            """)
            
            cursor.execute("""
                INSERT INTO events (timestamp, event_type, payload, status)
                VALUES (?, ?, ?, ?)
            """, (timestamp, event_type, payload_json, 'unread'))
            
            conn.commit()
            logger.info(f"Successfully published '{event_type}' event to Universal Router database.")
            
    except Exception as e:
        logger.error(f"Failed to publish event to database: {e}")
